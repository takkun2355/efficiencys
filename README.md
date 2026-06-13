# Process Control Tool

## 概要

Windowsプロセスの効率モードをGUIで制御するツール

---

## 機能

- プロセス一覧表示
- 選択プロセスの効率モード制御
- 管理者権限自動要求
- 日本語UI
- ログ出力（ターミナル）

---

## 必要環境

- Python 3.10+
- psutil

## 作成環境

- Python 3.11.9
- psutil 7.2.2
- uv 0.11.14

インストール：

```powershell
pip install psutil
```

uv使用時：

```powershell
uv add psutil
```

---

## 起動方法

```powershell
python main.py
```

uv使用時：

```powershell
uv run python main.py
```

または：

```powershell
uv run main.py
```

---

## 注意

- 管理者権限が必要
- 一部システムプロセス、サービスは変更不可
