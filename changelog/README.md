# MainShortcuts2
## 2.4.6 (29)
### Добавлено:
- Аргумент `cb_end` у функции `.utils.async_download_file`
- Аргумент `cb_end` у функции `.utils.sync_download_file`
- Аргумент `cb_progress` у функции `.utils.async_download_file`
- Аргумент `cb_progress` у функции `.utils.sync_download_file`
- Аргумент `cb_start` у функции `.utils.async_download_file`
- Аргумент `cb_start` у функции `.utils.sync_download_file`
- Аргумент `format` у функции `.utils.uuid`
- Класс `.api.base.BasicAuthClient`
- Класс `.api.webdav.WebDAVClient`
### Изменено:
- `.api.base.Base` переименован в `BaseClient` (старое название всё ещё доступно)
## 2.4.5 (28)
### Добавлено:
- Аргумент `session` у функции `.utils.sync_request`
- Свойство `time` у класса `.utils.MiddlewareBase`
- Функция `.term.countful_countdown`
- Функция `.term.iter_line`
- Функция `.term.patch_shell`
- Функция `.term.set_displayhook`
- Функция `.utils.disable_warnings`
## 2.4.4 (27)
### Добавлено:
- Аргумент `use_env` у функции `.utils.shebang_code`
- Декоратор `.utils.handle_exception`
- Класс `.advanced.CodeModule`
- Класс `.types.AutoaddDict`
## 2.4.3 (26)
### Добавлено:
- Аргумент `--sort` в скрипте `nano-json`
- Класс `.types.Color`
- Класс `.types.DotDict`
- Константа `.types.COLORS`
## 2.4.2 (25)
### Добавлено:
- Декоратор `.advanced.MultiLang.add_cache_builder`
- Класс `.advanced.DictScriptAction`
- Класс `.advanced.DictScriptRunner`
- Класс `.advanced.DictScriptVariable`
- Функция `.file.compare`
## 2.4.1 (24)
### Исправлено:
- Забыл поставить скобку в `__main__.py`
## 2.4.0 (23)
### Добавлено:
- Аргумент `-b` | `--bar` в скрипте `ms2-hash_check`
- Аргумент `-b` | `--bar` в скрипте `ms2-hash_gen`
- Аргументы `--encoding` и `--no-escape` в скрипте `nano-json`
- Подмодуль `.any2json`
## 2.3.3 (22)
### Исправлено:
- Забыл двоеточие поставить в `__main__.py`
## 2.3.2 (21)
### Исправлено:
- Глупая ошибка в скрипте `nano-json`
- Скрипт `ms2-hash_check`
- Скрипт `ms2-hash_gen`
## 2.3.1 (20)
### Добавлено:
- Аргумент `use_tmp_file` у функции `.file.save`
- Аргумент `use_tmp_file` у функции `.file.write`
- Атрибут `.use_tmp_file`
- Класс `.json.JsonFile`
- Константа `.json.MODES`
- Скрипт `nano-json`
- Скрипт `nginx-reload`
- Скрипт `nginx-restart`
- Функция `.utils.check_programs`
### Изменено:
- Поведение при аргументе `mode='print'` в `.json.encode`
## 2.3.0 (19)
### Добавлено:
- Метод `.path.Path.__fspath__`
- Подмодуль `.api`, импортируется вручную
- Функция `.term.set_title`
- Функция `.utils.get_self_module`
- Функция `.utils.multi_and`
- Функция `.utils.multi_or`
### Исправлено:
- Выход в `.utils.OnlyOneInstance` на других ОС
- Проверка в `.utils.OnlyOneInstance` на Windows
## 2.2.4 (18)
### Исправлено:
- Инициализация `.utils.OnlyOneInstance`
- Фильтрация расширений в `.dir.list`
## 2.2.3 (17)
### Добавлено:
- Аргумент `use_cache` в `.path.Path`
- Класс `.types.Action`
- Класс `.utils.OnlyOneInstance`
- Функция `.utils.remove_ANSI`
### Исправлено:
- Определение типа в `.cfg`
## 2.2.2 (16)
### Исправлено:
- Атрибут `.MAIN_DIR`
## 2.2.1 (15)
### Исправлено:
- Исправлено создание логгера при импорте ядра
## 2.2.0 (14)
### Добавлено:
- Атрибут `.MAIN_DIR`
- Атрибут `.MAIN_FILE`
- Подмодуль `.advanced`
- Подмодуль `.regex`
- Подмодуль `.special_chars`
- Функция `.utils.shebang_code`
- Функция `.utils.shebang_file`
### Изменено:
- Добавлено значение по умолчанию `ensure_ascii = False` в `.json.print`
## 2.1.3 (13)
### Добавлено:
- Класс `.path.TempFiles`
- Скрипт `ms2-import_example`
### Изменено:
- Свойство `.path.cwd` переделано в функцию
### Исправлено:
- `.path.Path.__init__` теперь преобразует путь к файлу в абсолютный
- Автоматическое определение типа в `.cfg`
## 2.1.2 (12)
### Добавлено:
- Аргумент `mkdir` у функции `.file.save`
- Аргумент `mkdir` у функции `.file.write`
- Аргумент `mkdir` у функции `.path.copy`
- Аргумент `mkdir` у функции `.path.link`
- Аргумент `mkdir` у функции `.path.move`
- Класс `.dir.TempDir`
## 2.1.1 (11)
### Добавлено:
- Функция `.term.disable_colors`
- Функция `.term.enable_colors`
- Функция `.win.hide_file`
- Функция `.win.unhide_file`
### Изменено:
- Добавлен аргумент `save_if_edited` к методу `.cfg.dload`
- Добавлен аргумент `save_if_edited` к методу `.cfg.fill_defaults`
## 2.1.0 (10)
### Добавлено:
- Подмодуль `.types`
## 2.0.9 (9)
### Исправлено:
- Функция `.dir.list`
## 2.0.8 (8)
### Исправлено:
- Функция `.dir.list`
## 2.0.7 (7)
### Исправлено:
- Функция `.dir.list`
## 2.0.6 (6)
### Добавлено:
- Документация на множество функций и методов
- Константа `.credits`
- Константа `.version`
- Метод `.cfg.get`
### Исправлено:
- Метод `.cfg.dload`
- Функция `.win.read_lnk`
- Функция `.win.write_lnk`
## 2.0.5 (5)
### Исправлено:
- Исправлена функция `.json.rewrite`
- Исправлена функция `.json.write`
## 2.0.4 (4)
### Изменено:
- Добавлен аргумент `follow` к методу `.path.Path.copy`
- Добавлен аргумент `follow` к методу `.path.Path.link`
- Добавлен аргумент `follow` к методу `.path.Path.move`
- Добавлен аргумент `follow` к методу `.path.Path.rename`
- Функция `.path.copy` возвращает путь назначения
- Функция `.path.link` возвращает путь назначения
- Функция `.path.move` возвращает путь назначения
- Функция `.path.rename` возвращает путь назначения
### Исправлено:
- Исправлен метод `.path.Path.in_dir`
- Исправлена функция `.json.write`
## 2.0.3 (3)
### Исправлено:
- Теперь нет проблем с импортом
## 2.0.2 (2)
### Исправлено:
- Исправлены (вроде) проблемы с импортом подмодулей
## 2.0.1 (1)
### Исправлено:
- Исправлена ошибка `TypeError: expected str, bytes or os.PathLike object, not NoneType` при импорте
## 2.0.0 (0)
### Добавлено:
- Создание модуля на основе `MainShortcuts`