# 🚀 PartiX - Big Data Partitioning Application

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![BeeWare Toga](https://img.shields.io/badge/GUI-BeeWare%20Toga-orange)
![Pandas](https://img.shields.io/badge/Data-Pandas-150458)


**PartiX** is a native cross-platform desktop application built with Python and BeeWare Toga. It is designed for smart, in-memory partitioning of large datasets (Big Data) without generating temporary files on disk.

---

## 📸 User Interface 

<img width="666" height="785" alt="image" src="https://github.com/user-attachments/assets/f5915b07-f5f5-4fbc-aba9-6cce8df57bf1" />


---

## ✨ Features

- **Multi-Format Upload**: Seamlessly imports `.csv`, `.xlsx`, `.xls`, `.html`, and `.txt` files in memory.
- **Flexible Partitioning Strategies**:
  - **By Rows (Quantity)**: Splits datasets into customizable chunks (`10`, `20`, `50`, `100`, `500`, or `1000` rows per file).
  - **By Unique Values / Groups (Column)**: Performs semantic grouping (Group-By) based on key columns (e.g., `Event Type`, `True IP Country`).
- **Dynamic Column Selection**: Checkboxes to select which specific columns to retain in output files.
- **Export Limits**: Allows capping the total number of exported sub-datasets for quick testing and sampling.
- **Instant In-Memory Export**: Direct ZIP compression in memory streams without disk I/O overhead.

---

## 📂 Project Structure


* **🛠️ Techniques Applied**
  * **In-Memory Streaming**: Operates entirely via memory buffers (`BytesIO` / `StringIO`), eliminating disk I/O overhead and temporary files.
  * **Chunked Data Processing**: Handles large files efficiently without exhausting RAM by processing records in controlled batches.
  * **Semantic Grouping (Group-By)**: Dynamically partitions data by categorical column values in addition to standard row-based chunking.

* **📚 Core Libraries & Dependencies**
  * **Pandas**: Powers multi-format data ingestion (`.csv`, `.xlsx`, `.xls`, `.html`, `.txt`), filtering, and chunking algorithms.
  * **BeeWare Toga**: Cross-platform Python GUI framework providing native desktop widgets and file system dialogs.
  * **ZipFile & IO**: Native Python modules handling real-time archive generation and byte-stream management.

* **🖥️ User Interface Capabilities**
  * **Zero-Path Configuration**: File selection via native OS dialogs without manual path typing.
  * **Dynamic Column Control**: Auto-generates interactive checkboxes from loaded dataset headers for instant column filtering.
  * **Custom Export Controls**: Provides options to switch partition strategies, set chunk limits, and trigger instant `.zip` downloads.
