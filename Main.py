import io
import os
import zipfile
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from typing import List, Generator
import pandas as pd


class SmartBigDataEngine:
    """Engine supporting Row-based Partitioning or Semantic Grouping (Group-By)."""

    def __init__(self, file_bytes: bytes, filename: str):
        self.buffer = io.BytesIO(file_bytes)
        self.filename = filename
        self.file_ext = filename.split('.')[-1].lower()

    def get_columns(self) -> List[str]:
        self.buffer.seek(0)
        if self.file_ext in ['csv', 'txt']:
            df = pd.read_csv(self.buffer, nrows=0)
            return [str(col) for col in df.columns]
        elif self.file_ext in ['xls', 'xlsx']:
            df = pd.read_excel(self.buffer, nrows=0)
            return [str(col) for col in df.columns]
        elif self.file_ext == 'html':
            dfs = pd.read_html(self.buffer)
            if not dfs:
                raise ValueError("No table found in the HTML file.")
            return [str(col) for col in dfs[0].columns]
        else:
            raise ValueError(f"Unsupported file extension: .{self.file_ext}")

    def partition_by_rows(self, selected_cols: List[str], chunk_size: int, max_files: int) -> io.BytesIO:
        """Traditional partitioning by chunk size (N rows)."""
        zip_buffer = io.BytesIO()
        self.buffer.seek(0)

        if self.file_ext in ['csv', 'txt']:
            chunks = pd.read_csv(self.buffer, chunksize=chunk_size)
        else:
            df_full = pd.read_excel(self.buffer) if self.file_ext in ['xls', 'xlsx'] else pd.read_html(self.buffer)[0]
            chunks = (df_full.iloc[i : i + chunk_size] for i in range(0, len(df_full), chunk_size))

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            part = 1
            for chunk in chunks:
                if max_files > 0 and part > max_files:
                    break
                valid_cols = [c for c in selected_cols if c in chunk.columns]
                filtered = chunk[valid_cols]
                csv_str = io.StringIO()
                filtered.to_csv(csv_str, index=False)
                zip_file.writestr(f"subbase_row_part_{part}.csv", csv_str.getvalue())
                part += 1

        zip_buffer.seek(0)
        return zip_buffer

    def partition_by_group(self, selected_cols: List[str], group_column: str, max_files: int) -> io.BytesIO:
        """Groups data by unique values of a specific column (e.g., Event Type, Country, Date)."""
        zip_buffer = io.BytesIO()
        self.buffer.seek(0)

        if self.file_ext in ['csv', 'txt']:
            df = pd.read_csv(self.buffer)
        elif self.file_ext in ['xls', 'xlsx']:
            df = pd.read_excel(self.buffer)
        elif self.file_ext == 'html':
            df = pd.read_html(self.buffer)[0]

        if group_column not in df.columns:
            raise ValueError(f"Grouping column '{group_column}' does not exist in the dataset.")

        valid_cols = [c for c in selected_cols if c in df.columns]

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            part = 1
            grouped = df.groupby(group_column)

            for group_value, group_df in grouped:
                if max_files > 0 and part > max_files:
                    break

                filtered = group_df[valid_cols]
                csv_str = io.StringIO()
                filtered.to_csv(csv_str, index=False)

                safe_group_name = str(group_value).replace('/', '_').replace('\\', '_').replace(':', '_')
                zip_file.writestr(f"subbase_group_{safe_group_name}.csv", csv_str.getvalue())
                part += 1

        zip_buffer.seek(0)
        return zip_buffer


class DataPartitionerApp(toga.App):

    def startup(self):
        self.engine = None
        self.checkbox_list = []
        self.file_bytes = None
        self.file_name = None

        self.main_window = toga.MainWindow(title="PartiX", size=(680, 780))

        # --- Header (Centralizado e Estilizado) ---
        lbl_title = toga.Label(
            "🚀 PartiX",
            style=Pack(font_size=24, font_weight="bold", text_align=CENTER, margin_bottom=2)
        )
        lbl_subtitle = toga.Label(
            "Big Data Partitioning Application",
            style=Pack(font_size=12, font_style="italic", text_align=CENTER, margin_bottom=15)
        )

        # --- Seção 1: Upload ---
        self.btn_upload = toga.Button(
            "📂 Select Dataset File",
            on_press=self.on_select_file,
            style=Pack(height=35, margin_bottom=5)
        )
        self.lbl_filename = toga.Label(
            "⚠️ No file loaded yet",
            style=Pack(font_style="italic", text_align=CENTER, margin_bottom=15)
        )

        # --- Seção 2: Configurações de Particionamento ---
        lbl_mode = toga.Label(
            "⚙️ Partitioning Strategy:",
            style=Pack(font_weight="bold", margin_top=5, margin_bottom=5)
        )
        self.select_mode = toga.Selection(
            items=["By Rows (Quantity)", "By Unique Values / Groups (Column)"],
            style=Pack(width=320, margin_bottom=10)
        )

        lbl_range = toga.Label("  • Rows per file (if By Rows):", style=Pack(margin_right=10))
        self.select_range = toga.Selection(items=["10", "20", "50", "100", "500", "1000"], style=Pack(width=100))
        self.select_range.value = "50"
        box_range = toga.Box(style=Pack(direction=ROW, margin_bottom=8), children=[lbl_range, self.select_range])

        lbl_group_col = toga.Label("  • Column to Group By (if By Groups):", style=Pack(margin_right=10))
        self.select_group_col = toga.Selection(items=["Load a file first"], style=Pack(width=200))
        box_group = toga.Box(style=Pack(direction=ROW, margin_bottom=8), children=[lbl_group_col, self.select_group_col])

        lbl_limit = toga.Label("  • Export limit (0 = no limit):", style=Pack(margin_right=10))
        self.input_max_files = toga.TextInput(value="0", style=Pack(width=100))
        box_limit = toga.Box(style=Pack(direction=ROW, margin_bottom=15), children=[lbl_limit, self.input_max_files])

        # --- Seção 3: Seleção de Colunas ---
        lbl_cols = toga.Label(
            "📋 Select columns to keep in exported files:",
            style=Pack(font_weight="bold", margin_top=5, margin_bottom=5)
        )
        self.box_columns = toga.Box(style=Pack(direction=COLUMN, margin_bottom=10))
        self.scroll_columns = toga.ScrollContainer(horizontal=False, style=Pack(height=180, margin_bottom=15))
        self.scroll_columns.content = self.box_columns

        # --- Seção 4: Ação de Exportação ---
        self.btn_export = toga.Button(
            "⚡ Partition and Export (.zip)",
            on_press=self.on_export_partition,
            enabled=False,
            style=Pack(font_weight="bold", height=45)
        )

        main_box = toga.Box(
            style=Pack(direction=COLUMN, margin=20),
            children=[
                lbl_title,
                lbl_subtitle,
                self.btn_upload,
                self.lbl_filename,
                lbl_mode,
                self.select_mode,
                box_range,
                box_group,
                box_limit,
                lbl_cols,
                self.scroll_columns,
                self.btn_export
            ]
        )

        self.main_window.content = main_box
        self.main_window.show()

    async def on_select_file(self, widget):
        try:
            file_path = await self.main_window.open_file_dialog(
                title="Select Dataset",
                file_types=["csv", "xlsx", "xls", "html", "txt"]
            )
            if not file_path:
                return

            self.file_name = os.path.basename(str(file_path))
            with open(file_path, "rb") as f:
                self.file_bytes = f.read()

            self.engine = SmartBigDataEngine(self.file_bytes, self.file_name)
            self.lbl_filename.text = f"✅ Loaded file: {self.file_name}"

            cols = self.engine.get_columns()

            self.select_group_col.items = cols

            self.box_columns.clear()
            self.checkbox_list = []
            for col in cols:
                cb = toga.Switch(text=f"  {col}", value=True, style=Pack(margin=2))
                self.checkbox_list.append(cb)
                self.box_columns.add(cb)

            self.btn_export.enabled = True

        except Exception as e:
            await self.main_window.dialog(
                toga.ErrorDialog("Loading Error", f"Failed to open file:\n{str(e)}")
            )

    async def on_export_partition(self, widget):
        if not self.engine:
            return

        selected_cols = [cb.text.strip() for cb in self.checkbox_list if cb.value]
        if not selected_cols:
            await self.main_window.dialog(toga.ErrorDialog("Warning", "Select at least one column."))
            return

        try:
            max_files = int(self.input_max_files.value)
        except ValueError:
            await self.main_window.dialog(toga.ErrorDialog("Error", "Export limit must be an integer."))
            return

        mode = self.select_mode.value

        try:
            if "By Rows" in mode:
                chunk_size = int(self.select_range.value)
                zip_buffer = self.engine.partition_by_rows(
                    selected_cols=selected_cols,
                    chunk_size=chunk_size,
                    max_files=max_files
                )
            else:
                group_col = str(self.select_group_col.value)
                zip_buffer = self.engine.partition_by_group(
                    selected_cols=selected_cols,
                    group_column=group_col,
                    max_files=max_files
                )

            save_path = await self.main_window.save_file_dialog(
                title="Save ZIP Package",
                suggested_filename="partitioned_subbases.zip",
                file_types=["zip"]
            )

            if save_path:
                with open(save_path, "wb") as f:
                    f.write(zip_buffer.getvalue())
                await self.main_window.dialog(
                    toga.InfoDialog("Success", "🎉 Sub-datasets generated and exported successfully!")
                )

        except Exception as e:
            await self.main_window.dialog(
                toga.ErrorDialog("Error", f"Partitioning failed:\n{str(e)}")
            )


def main():
    return DataPartitionerApp("PartiX", "org.beeware.partix")


if __name__ == "__main__":
    main().main_loop()
