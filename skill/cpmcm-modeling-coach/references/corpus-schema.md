# 语料结构

`references/corpus-index.json` 是开源版的匿名精读笔记索引。每条记录包含：`paper_id`、`year`、`problem_code`、`file_name`、`page_count`、`reading_status`、`availability` 和 `note_path`。

逐篇精读笔记包含：题面对应、摘要主张、逐小问模型链、关键公式/参数、数据处理、验证、数值结果、可复用思想、缺陷、复现依赖、页码证据和当前状态。

校验索引与精读笔记：

```powershell
python scripts/validate_corpus.py
```

检索：

```powershell
python scripts/query_corpus.py --year 2023 --problem C
python scripts/query_corpus.py --status full_read
```

本开源版固定包含33篇 `full_read` 结构化笔记，但不附第三方论文PDF。索引和笔记为只读资料；用户自行提供合法论文原文后，可按匿名编号建立对应关系。

PDF渲染、文字抽取和建模中间物应存入当前赛题项目目录，而不是写入Skill。需要引用或核验原论文时必须读取用户提供的合法副本，不能仅凭笔记补写原文内容。
