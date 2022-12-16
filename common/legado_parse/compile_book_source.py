# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/12/16
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
# 将词法分析的规则进行分组

from LegadoParser2.RuleType import RuleType, getRuleTypeForGroup, getRuleType
from LegadoParser2.Tokenize2 import tokenizer, tokenizerInner, splitPage
from LegadoParser2.RuleDefault.RuleDefaultEfficient2 import parseIndex, getElementsXpath
from LegadoParser2.RuleDefault.EndRule import EndRuleXpath
from lxml.etree import _Element, tostring, XPath, XPathSyntaxError
from cssselect import SelectorSyntaxError, ExpressionError
from LegadoParser2.RuleJsonPath.RuleJsonPath import getJsonPath
from jsonpath_ng.exceptions import JSONPathError
import re
from LegadoParser2 import GSON
from LegadoParser2.config import DEBUG_MODE
from copy import deepcopy


def groupTokensByType(rulesTokens):
    """
    对规则进行分组
    """
    groupRules = []
    length = len(rulesTokens)
    cursor = 0

    while cursor < length:
        ruleType = getRuleTypeForGroup(rulesTokens, cursor)

        ruleTokens, cursor = groupTokens(rulesTokens, cursor, ruleType)
        groupRules.append(ruleTokens)

        cursor += 1
    return groupRules


def groupTokens(rulesTokens, cursor, ruleType):
    ruleTokens = {"type": ruleType, "tokens": []}
    length = len(rulesTokens)
    while cursor < length:
        rT = getRuleTypeForGroup(rulesTokens, cursor)
        if rT == ruleType or rT == RuleType.JoinSymbol:
            ruleTokens["tokens"].append(rulesTokens[cursor])
        else:
            cursor -= 1
            break
        cursor += 1
    return ruleTokens, cursor


# 预处理规则
def preProcessRule(groupedRules):
    """
    对packet函数返回的规则进行预处理

    参数：
      packedRules - packet函数返回的list



    """
    # 1、处理 && %% || 连接符号
    for groupedRule in groupedRules:
        groupedRule["joinSymbol"] = ""
        groupedRule["crossJoin"] = False  # 跨规则组拼接
        subRules = []
        subRule = []
        for i in groupedRule["tokens"]:
            if i in {"&&", "||", "%%"}:
                if not groupedRule["joinSymbol"]:
                    groupedRule["joinSymbol"] = i
                subRules.append(subRule)
                subRule = []
                continue
            subRule.append(i)
        subRules.append(subRule)
        if not subRules[-1]:
            del subRules[-1]
            groupedRule["crossJoin"] = True
        subRules = list(filter(None, subRules))
        groupedRule["subRules"] = subRules

    # 2、对规则进行预处理，主要是编译xpath jsonpath regex
    captureGroupRegex = re.compile(r"(?<!\\)\$\d")
    for rule in groupedRules:
        rule["preProcess"] = {}
        if rule["type"] == RuleType.DefaultOrEnd:
            rule["preProcess"] = {"subRules": []}
            for subRule in rule["subRules"]:
                rule["preProcess"]["subRules"].append(compileRule(subRule))
        elif rule["type"] == RuleType.Xpath:
            rule["preProcess"] = {"subRules": []}
            for subRule in rule["subRules"]:
                rule["preProcess"]["subRules"].append(compileRule(subRule))
        elif rule["type"] == RuleType.Json:
            rule["preProcess"] = {"subRules": []}
            for subRule in rule["subRules"]:
                rule["preProcess"]["subRules"].append(compileRule(subRule))
        elif rule["type"] == RuleType.Regex:
            rule["preProcess"] = {
                "regexType": "",
                "body": {
                    "regex": "",
                    "reObj": None,
                    "replacement": "",
                    "replaceFirst": False,
                },
            }
            regexRule = rule["subRules"][0]
            length = len(regexRule)

            # ## regex 形式
            if length > 1:
                rule["preProcess"]["body"]["regex"] = regexRule[1]

            # ## regex ## replacement 形式
            if length > 3:
                rule["preProcess"]["body"]["replacement"] = regexRule[3]

            # 先假定为replace模式
            rule["preProcess"]["regexType"] = "replace"

            if length == 5 and regexRule[-1] == "###":
                rule["preProcess"]["regexType"] = "onlyOne"

            elif length == 2 and regexRule[0] == ":":
                rule["preProcess"]["regexType"] = "allInOne"

            elif length == 5 and regexRule[-1] == "##":
                rule["preProcess"]["body"]["replaceFirst"] = True

            elif length == 3 and regexRule[-1] == "####":
                rule["preProcess"]["body"]["replaceFirst"] = True

            if rule["preProcess"]["body"]["regex"]:
                try:
                    rule["preProcess"]["body"]["reObj"] = re.compile(
                        rule["preProcess"]["body"]["regex"]
                    )
                except re.error:
                    if DEBUG_MODE:
                        print("preProcessRule 正则表达式编译失败")
                    pass

            if (
                    rule["preProcess"]["body"]["replacement"]
                    and rule["preProcess"]["regexType"] == "replace"
            ):
                rule["preProcess"]["body"]["replacement"] = captureGroupRegex.sub(
                    lambda x: "\\" + x[0][1], rule["preProcess"]["body"]["replacement"]
                )

        elif rule["type"] == RuleType.Js:
            rule["preProcess"] = {
                "hasInnerRule": False,
                "js": [],
                "innerRules": [],
                "compiledRules": [],
            }
            for js in rule["tokens"]:
                if js in {"@js:", "<js>", "</js>"}:
                    continue
                tokenResult = tokenizerInner(js)
                if len(tokenResult) > 1:
                    rule["preProcess"]["hasInnerRule"] = True
                rule["preProcess"]["js"].append(tokenResult)
                length = len(tokenResult)
                cursor = 0
                innerRule = []
                while cursor < length:
                    ruleType = getRuleType(tokenResult, cursor)
                    if ruleType == RuleType.Inner:
                        innerRule.append((tokenResult[cursor], cursor))
                    cursor += 1
                rule["preProcess"]["innerRules"].append(innerRule)

            for i in rule["preProcess"]["innerRules"]:
                compiledRule = []
                for y in i:
                    compiledRuleObj = getRuleObj([y[0]])
                    r = compiledRuleObj[0]
                    if r["type"] == RuleType.DefaultOrEnd and r["tokens"][0] not in {
                        "@",
                        "@@",
                    }:
                        r["type"] = RuleType.Js  # Inner默认规则为Js
                        r["preProcess"]["js"] = [r["tokens"]]
                        r["preProcess"]["innerRules"] = []
                        r["preProcess"]["compiledRules"] = []
                    compiledRule.append(compiledRuleObj)
                rule["preProcess"]["compiledRules"].append(compiledRule)
        elif rule["type"] == RuleType.Format:
            rule["preProcess"] = {"subRules": []}
            for subRule in rule["subRules"]:
                formatObj = {
                    "innerRules": [],
                    "getRules": [],
                    "regexRules": [],
                    "jsonRules": [],
                    "pageRules": [],
                    "compiledInnerRules": [],
                    "compiledJsonRules": [],
                    "compiledPageRules": [],
                }
                length = len(subRule)
                cursor = 0
                while cursor < length:
                    ruleType = getRuleType(subRule, cursor)
                    if ruleType == RuleType.Inner:
                        formatObj["innerRules"].append((subRule[cursor], cursor))
                    elif ruleType == RuleType.Get:
                        formatObj["getRules"].append((subRule[cursor], cursor))
                    elif ruleType == RuleType.Regex:
                        # allInOne 的 $1
                        formatObj["regexRules"].append((subRule[cursor], cursor))
                    elif ruleType == RuleType.JsonInner:
                        formatObj["jsonRules"].append((subRule[cursor], cursor))
                    elif ruleType == RuleType.Page:
                        formatObj["pageRules"].append((subRule[cursor], cursor))
                    cursor += 1
                for i in formatObj["innerRules"]:
                    formatObj["compiledInnerRules"].append(getRuleObj(i[0]))
                for i in formatObj["jsonRules"]:
                    formatObj["compiledJsonRules"].append(getRuleObj(i[0]))
                for i in formatObj["pageRules"]:
                    pageRuleList = splitPage(i[0])
                    for page in pageRuleList:
                        page = page.strip()
                        if "{{" in page:
                            formatObj["compiledPageRules"].append(getRuleObj(page))
                        else:
                            formatObj["compiledPageRules"].append(page)
                rule["preProcess"]["subRules"].append(formatObj)
        elif rule["type"] == RuleType.Put:
            rule["preProcess"] = {"putRules": {}, "compiledPutRules": {}}
            length = len(rule["subRules"][0])
            if length == 3:
                rule["preProcess"]["putRules"] = GSON.parse(
                    "{" + rule["subRules"][0][1] + "}"
                )
                for key, value in rule["preProcess"]["putRules"].items():
                    rule["preProcess"]["compiledPutRules"][key] = getRuleObj(value)
        elif rule["type"] == RuleType.Order:
            rule["preProcess"] = {"reverse": False}
            if rule["tokens"][0] == "-":
                rule["preProcess"]["reverse"] = True

    return groupedRules


def compileRule(rules):
    length = len(rules)
    cursor = 0
    compiledRules = []

    while cursor < length:
        ruleType = getRuleType(rules, cursor)
        ruleObj = {
            "rule": rules[cursor],
            "type": ruleType,
            "parsedIndex": None,
            "xpath": None,
            "endXpath": None,
            "jsonPath": None,
            "regex": None,
            "replacement": None,
        }

        if ruleType == RuleType.DefaultOrEnd:
            indexList, endPos = parseIndex(rules[cursor])

            ruleObj["parsedIndex"] = (indexList, endPos)
            ruleObj["rule"] = rules[cursor][:endPos]
            try:
                path = getElementsXpath(rules[cursor][:endPos])
                if path:
                    ruleObj["xpath"] = XPath(path)
            except XPathSyntaxError:
                pass
            except SelectorSyntaxError as e:
                if DEBUG_MODE:
                    print(f"css 错误{e}")
                pass
            except ExpressionError as e:
                if DEBUG_MODE:
                    print(f"不支持的选择器：{e}")
                    raise
                pass
            except IndexError:
                pass
            try:
                if cursor + 1 == length or rules[cursor + 1] in {"&&", "%%", "||"}:
                    ruleObj["endXpath"] = EndRuleXpath.get(rules[cursor])

            except XPathSyntaxError:
                pass

            try:
                if length == 1:
                    ruleObj["jsonPath"] = getJsonPath(rules[cursor])
            except JSONPathError:
                pass

        elif ruleType == RuleType.Xpath:
            try:
                path = rules[cursor]
                if path[0] != ".":
                    path = "." + path
                ruleObj["xpath"] = XPath(path)
            except XPathSyntaxError as e:
                pass
                # print(f'compileRule 发生异常 {e}')

        elif ruleType == RuleType.Json:
            try:
                ruleObj["jsonPath"] = getJsonPath(rules[cursor])
            except JSONPathError as e:
                if DEBUG_MODE:
                    print(f"compileRule 解析jsonpath失败 {e}")
                pass

        cursor += 1
        compiledRules.append(ruleObj)
    return compiledRules


def getRuleObj(rule):
    return preProcessRule(groupTokensByType(tokenizer(rule)))


def trimBookSource(bS):
    for k in bS:
        if isinstance(bS[k], str):
            bS[k] = bS[k].strip()
        elif isinstance(bS[k], dict):
            trimBookSource(bS[k])


def compileBookSource(bookSource, specify=""):
    bookSource = deepcopy(bookSource)
    trimBookSource(bookSource)
    ruleGroupNames = ("ruleSearch", "ruleBookInfo", "ruleToc", "ruleContent")
    excludeRuleSet = {
        "checkKeyWord",
        "canReName",
        "webJs",
        "imageStyle",
        "sourceRegex",
        "payAction",
    }
    if specify in bookSource:
        for key in bookSource[specify]:
            if key in excludeRuleSet:
                continue
            if bookSource[specify][key]:
                bookSource[specify][key] = getRuleObj(bookSource[specify][key])
    else:
        for ruleGroupName in ruleGroupNames:
            for key in bookSource[ruleGroupName]:
                if key in excludeRuleSet:
                    continue
                if bookSource[ruleGroupName][key]:
                    bookSource[ruleGroupName][key] = getRuleObj(
                        bookSource[ruleGroupName][key]
                    )
    return bookSource
