# Проверка первичной постановки

Повторно прочитано официальное условие (artifacts/official_statement.txt, PDF SHA в PROBLEM_AUDIT.json) и функции официального task/validate_solution.py. Максимизируется reward−distance−cost−α·range(task_load); maxSize и maxDifference ограничивают число сайтов. Назначенные работники обязаны реально покрывать навыки и не могут делиться между офисами. Геометрическая проверка использует covers всех входных точек сайтов и офисов, включая границы, закрытые и неназначенные точки. Пересечение в области без общих входных точек допускается.

| Ручная проверка | Ожидается и получено |
|---|---|
| profitable | 5.0 |
| unprofitable | -5.0 |
| empty | 0.0 |
| open_two_offices_cost5 | 15.0 |
| equal_site_count_unequal_task_load | -285.0 |
| before_negative | 10.0 |
| negative_site_reduces_penalty | 35.0 |
| capacity_counts_sites | 10.0 |
| capacity_violation | Office capacity exceeded |
| site_count_imbalance | Site-count imbalance |
| actual_worker_required | Missing skills |
| crossing_without_input_point_allowed | 20.0 |
| unassigned_site_on_both_boundaries | Hull conflict |
| closed_office_on_both_boundaries | Hull conflict |
| worker_cannot_be_shared | Duplicate worker |

15/15 совпадений. Это тесты фиксированных ручных ответов против валидатора, не15 запусков решателя и не прирост качества. Полные маленькие входы и ответы сохранены; записи копируются целиком при создании, последующая смена α не меняет ранние примеры.
