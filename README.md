# pesquisasgtcontabilidadegefin
Portal de Pesquisas GT 06 Contabilidade GEFIN

## Controle permanente de duplicidade por estado (UF)

Antes de atualizar a pre-analise estatistica, execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verificar-duplicidades.ps1
```

Esse comando atualiza automaticamente:

- `memoria-duplicidades.json`
- `memoria-duplicidades.md`

Regra do projeto:

- Sempre apontar no resumo da pre-analise quando houver UF em duplicidade.
- Consolidar indicadores por UF unica (priorizando a resposta mais recente quando houver repeticao do mesmo estado).
