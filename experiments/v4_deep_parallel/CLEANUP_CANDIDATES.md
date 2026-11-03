# Необязательные кандидаты на очистку

**Ничего не удалено. Разрешение на удаление не запрашивается, потому что очистка не выполняется.**

Сохранены все проверенные бинарники, исходники, входы, ответы, логи, manifests,
отрицательные результаты и оба ZIP. Проверенные бинарники оставлены намеренно:
их удаление сделает исторические пути в manifests недоступными до восстановления.

Ниже только воспроизводимые кеши и подтверждённые копии. Этот список сам по себе
не является разрешением на удаление. Исторические manifests не переписываются.

| Файл | Байт | Почему воспроизводим / дубликат |
|---|---:|---|
| `experiments/v4_deep_parallel/geometry/src/__pycache__/repair_mip_allopts.cpython-314.pyc` | 40983 | Python import cache; regenerated from retained .py sources. |
| `experiments/v4_deep_parallel/integration/__pycache__/plot_trajectories.cpython-314.pyc` | 12606 | Python import cache; regenerated from retained .py sources. |
| `experiments/v4_deep_parallel/integration/__pycache__/summarize.cpython-314.pyc` | 6161 | Python import cache; regenerated from retained .py sources. |
| `experiments/v4_deep_parallel/integration/__pycache__/territory_model.cpython-314.pyc` | 14484 | Python import cache; regenerated from retained .py sources. |
| `experiments/v4_deep_parallel/integration/artifacts/zip_rebuild/Makefile` | 75 | Byte-identical extracted copy of retained package file and ZIP payload. |
| `experiments/v4_deep_parallel/integration/artifacts/zip_rebuild/frozen.normalized` | 474848 | ELF comparison copy, reproducible from retained binary via objcopy; recorded hashes are preserved. |
| `experiments/v4_deep_parallel/integration/artifacts/zip_rebuild/main.cpp` | 185146 | Byte-identical extracted copy of retained package file and ZIP payload. |
| `experiments/v4_deep_parallel/integration/artifacts/zip_rebuild/package.normalized` | 474848 | ELF comparison copy, reproducible from retained binary via objcopy; recorded hashes are preserved. |

Всего кандидатов: 8, 1,209,151 байт.

Полная инвентаризация с SHA256: `INVENTORY.json`.
