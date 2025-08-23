# MainShortcuts2
## 2.6.0 (48)
### Добавлено:
- Класс `.win.RegExplorer`
- Класс `.win.RegFastLocations`
- Класс `.win.RegFolder`
- Класс `.win.RegFolderAuto`
- Класс `.win.RegFolderJson`
- Класс `.win.utils`
- Константа `.win.ENV_SYSTEM`
- Константа `.win.ENV_SYSTEM64`
- Константа `.win.ENV_USER`
- Константа `.win.REG_LOC_BY_NAME`
- Константа `.win.REG_LOC_BY_NUM`
- Подмодуль `.linux`
- Свойство `.advanced.PlatformInfo.user_desktop_dir`
- Свойство `.advanced.PlatformLinux.system_hosts_file`
- Свойство `.advanced.PlatformWindows.system_hosts_file`
- Функция `.win.reg_loc2path`
- Функция `.win.reg_path2loc`
- Функция `.win.reg_prep_path`
## 2.5.9 (47)
### Добавлено:
- Метод `.utils.MultiContext.add_obj`
### Исправлено:
- Метод `.utils.MultiContext.__enter__`
## 2.5.8 (46)
### Исправлено:
- Ещё фатальная ошибка. Я вообще программист?
## 2.5.7 (45)
### Исправлено:
- Фатальная ошибка при импорте
## 2.5.6 (44)
### Добавлено:
- Добавлена проверка наличия обновлений (отключается в конфиге или environ `MS2_NO_UPDATE`)
- Метод `.cfg.save_if_need`
- Метод `.cfg.setdefault`
- Переменная `.cfg.need_save`
- Поддержка асинхронных функций в `.utils.main_func`
- Создание папки в методе `.cfg.save`
### Исправлено:
- Метод `.advanced.FileDownloader.add_handler`
## 2.5.5 (43)
### Исправлено:
- Получение папок в `.advanced.PlatformTermux`
## 2.5.4 (42)
### Исправлено:
- Ошибка в классе `.advanced.PlatformInfo`
## 2.5.3 (41)
### Добавлено:
- Декоратор `.utils.generator2list`
- Класс `.advanced._Platform`
- Класс `.advanced.PlatformInfo`
- Класс `.advanced.PlatformLinux`
- Класс `.advanced.PlatformMacOS`
- Класс `.advanced.PlatformTermux`
- Класс `.advanced.PlatformWindows`
- Класс `.api.base.CacheStorage`
- Метод `.path.Path.hash_hex`
- Метод `.path.Path.hash`
- Метод `.path.Path.list_dir_iter`
- Метод `.path.Path.multi_hash_hex`
- Метод `.path.Path.multi_hash`
- Метод `.path.Path.open_file`
- Переменная `.api.base.BaseClient.cache`
- Функция `.advanced.get_platform`
- Функция `.utils.mini_log`
- Функция `.utils.print_stderr`
- Функция `.utils.setattr_if_not_exists`
- Функция/декоратор `.utils.call`
## 2.5.2 (40)
### Добавлено:
- Аргумент `resume` для метода `.advanced.FileDownloader.download2file`
- Класс `.utils.MultiContext`
- Метод `.advanced.FileDownloader.download2func`
- Метод `.advanced.FileDownloader.download2null`
- Метод `.advanced.FileDownloader.h_hash`
- Метод `.advanced.FileDownloader.h_progressbar`
- Функция `.utils.http_check_range_support`
## 2.5.1 (39)
### Исправлено:
- Фатальная ошибка отступа в новых свойствах
## 2.5.0 (38)
### Добавлено:
- Класс `.advanced.FileDownloader` (не проверен)
- Подмодуль `.ms2app` (не проверен)
- Подмодуль `.ms2hash`
- Подмодуль `.sql`, импортируется вручную
- Свойства `.now_dt`, `.now`, `.utcnow_dt` и `.utcnow`
- Скрипт `ms2-app` (не проверен)
## 2.4.14 (37)
### Добавлено:
- Декоратор `.utils.OnlyOneInstance.wrap_func`
- Класс `.api.base.ObjectBase`
- Класс `.ObjectBase`
- Функция `.utils.add2pythonpath`
- Функция `.utils.auto_install_modules`
- Функция `.utils.check_modules`
- Функция `.utils.run_pip`
## 2.4.13 (36)
### Исправлено:
- Фильтр в функции `.dir.list_iter`
- Фильтр в функции `.dir.recursive_list_iter`
## 2.4.12 (35)
### Исправлено:
- Рекурсивный вызов функции `.dir.list`
## 2.4.11 (34)
### Добавлено:
- Метод `.path.Path.__lt__`
- Метод `.path.Path.list_dir`
- Метод `.path.Path.to_dict`
- Метод `.proc.Popen.force_wait`
- Метод `.proc.Popen.wait_on_bg`
- Функция `.dir.list_iter`
- Функция `.dir.recursive_list_iter`
- Функция `.dir.recursive_list`
## 2.4.10 (33)
### Добавлено:
- Класс `.path.Stat`
- Скрипт `ms2-ln`
- Функция `.utils.fassert`
### Изменено:
- Декоратор `.utils.main_func` теперь обрабатывает KeyboardInterrupt
### Исправлено:
- Скрипты `ms2-hash_gen` и `ms2-hash_check` больше не пытаются открыть папку как файл
## 2.4.9 (32)
### Добавлено:
- Декоратор `.utils.main_func`
- Класс `.utils.decorators`
- Константа `.api.base.USER_AGENTS`
- Функция `.utils.restore_deprecated`
## 2.4.8 (31)
### Добавлено:
- Функция `.utils.is_instance_of_all`
- Функция `.utils.is_instance_of_one`
### Исправлено:
- Поломка скрипта `nano-json`
- Создание хеша для хеша в скрипте `ms2-hash_gen`
## 2.4.7 (30)
### Добавлено:
- Аргумент `--force` в скрипте `ms2-hash_gen`
- Класс `.win.LnkFile`
- Функция `.path.readlink`
### Исправлено:
- Исправлена запись файлов, которые являются ссылками
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