## 变更内容

请简要说明这次 PR 做了什么。

## 影响范围

- [ ] docs
- [ ] canonical scaffold
- [ ] scripts
- [ ] tests
- [ ] CI

## 验证

请填写你实际运行过的命令和结果。

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q
```

## 风险与注意事项

请说明：

- 是否修改了 canonical contract
- 是否涉及 schema drift
- 是否需要更新 spec / handoff 文档
