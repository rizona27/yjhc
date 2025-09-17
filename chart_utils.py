# chart_utils.py
import matplotlib.dates as mdates
from matplotlib.ticker import StrMethodFormatter, MaxNLocator
import matplotlib.pyplot as plt
from datetime import datetime

class ChartUtils:
    def __init__(self, app):
        self.app = app
        self.config = app.config
        self.hover_line_x = None
        self.hover_line_y = None
        self.hover_marker = None
        self.hover_text_obj = None
        self.hover_date_marker = None
        self.max_min_text_obj = []

    def initialize_chart(self):
        self.app.ax.clear()
        self.app.current_plot_data = None  # 清空当前图表数据

        if self.hover_line_x:
            try:
                self.hover_line_x.remove()
            except:
                pass
            self.hover_line_x = None

        if self.hover_line_y:
            try:
                self.hover_line_y.remove()
            except:
                pass
            self.hover_line_y = None

        if self.hover_marker:
            try:
                self.hover_marker.remove()
            except:
                pass
            self.hover_marker = None

        if self.hover_text_obj:
            try:
                self.hover_text_obj.remove()
            except:
                pass
            self.hover_text_obj = None

        if self.max_min_text_obj:
            for text_obj in self.max_min_text_obj:
                try:
                    text_obj.remove()
                except:
                    pass
            self.max_min_text_obj = []

        self.app.figure.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.35)
        self.app.figure.tight_layout(pad=1.5)

        self.app.ax.tick_params(axis='x',
                           which='major',
                           labelsize=4,
                           colors=self.config.colors["text"])
        self.app.ax.tick_params(axis='y',
                           which='major',
                           labelsize=5,
                           colors=self.config.colors["text"])
        self.app.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.4f}'))
        self.app.ax.yaxis.set_major_locator(MaxNLocator(prune='both', nbins=5))

        self.app.ax.grid(True,
                    linestyle='--',
                    alpha=0.6,
                    color=self.config.colors["chart_grid"])

        self.app.ax.spines['top'].set_visible(False)
        self.app.ax.spines['right'].set_visible(False)
        self.app.ax.spines['left'].set_color(self.config.colors["text_light"])
        self.app.ax.spines['bottom'].set_color(self.config.colors["text_light"])  

        plt.setp(self.app.ax.get_xticklabels(), rotation=30, ha='right', fontsize=4)

        self.app.canvas.draw()

    def setup_chart_formatting(self, df_plot):
        """设置图表格式"""
        date_range = df_plot['日期'].max() - df_plot['日期'].min()
        days = date_range.days

        if days <= 30:
            date_format = '%m-%d'
            interval = max(1, int(days/7))
            locator = mdates.DayLocator(interval=interval)
        elif days <= 180:
            date_format = '%m-%d'
            interval = max(1, int(days/10))
            locator = mdates.DayLocator(interval=interval)
        elif days <= 365:
            date_format = '%m-%d'
            locator = mdates.MonthLocator()
        else:
            date_format = '%Y-%m'
            locator = mdates.MonthLocator(interval=3)

        self.app.ax.xaxis.set_major_locator(locator)
        self.app.ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))

        min_nav = df_plot['单位净值'].min()
        max_nav = df_plot['单位净值'].max()
        nav_range = max_nav - min_nav

        if nav_range > 0:
            buffer = nav_range * 0.05
            self.app.ax.set_ylim(min_nav - buffer, max_nav + buffer)

        self.app.ax.yaxis.set_major_locator(MaxNLocator(prune='both', nbins=5))

        self.app.ax.grid(True,
                    linestyle='--',
                    alpha=0.6,
                    color=self.config.colors["chart_grid"])

        self.app.ax.tick_params(axis='x',
                           which='major',
                           labelsize=4,
                           colors=self.config.colors["text"])
        self.app.ax.tick_params(axis='y',
                           which='major',
                           labelsize=5,
                           colors=self.config.colors["text"])
        self.app.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.4f}'))

        self.app.ax.spines['top'].set_visible(False)
        self.app.ax.spines['right'].set_visible(False)
        self.app.ax.spines['left'].set_color(self.config.colors["text_light"])
        self.app.ax.spines['bottom'].set_color(self.config.colors["text_light"])  

        plt.setp(self.app.ax.get_xticklabels(), rotation=30, ha='right', fontsize=4)

        self.app.figure.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.35)
        self.app.figure.tight_layout(pad=1.5)

    def on_hover(self, event):
        """处理鼠标悬停事件，显示日期和净值，并绘制十字虚线"""
        # 如果有设置的悬停日期，则不显示鼠标悬停数据
        if self.config.get("show_hover_data") and self.config.get("hover_date"):
            return
            
        # 使用当前显示的图表数据而不是完整数据集
        if self.app.current_plot_data is None or event.inaxes != self.app.ax:
            self.on_leave(event)
            return

        try:
            # 移除旧的悬停标注和标记
            if self.hover_text_obj:
                self.hover_text_obj.remove()
                self.hover_text_obj = None
            if self.hover_line_x:
                self.hover_line_x.remove()
                self.hover_line_x = None
            if self.hover_line_y:
                self.hover_line_y.remove()
                self.hover_line_y = None
            if self.hover_marker:
                self.hover_marker.remove()
                self.hover_marker = None

            xdata_date = mdates.num2date(event.xdata).replace(tzinfo=None)

            # 找到最近的日期数据点 - 使用当前显示的图表数据
            closest_idx = self.app.current_plot_data['日期'].sub(xdata_date).abs().idxmin()

            closest_row = self.app.current_plot_data.loc[closest_idx]
            nav = closest_row['单位净值']
            date = closest_row['日期']

            # 绘制新的十字虚线 (透明度设为0.5)
            self.hover_line_x = self.app.ax.axvline(
                x=date,
                color=self.config.colors["chart_hover"],
                linestyle='--',
                linewidth=1,
                alpha=0.5,
                zorder=5
            )

            self.hover_line_y = self.app.ax.axhline(
                y=nav,
                color=self.config.colors["chart_hover"],
                linestyle='--',
                linewidth=1,
                alpha=0.5,
                zorder=5
            )

            # 绘制新的空心圆
            self.hover_marker, = self.app.ax.plot(
                date,
                nav,
                marker='o',
                markersize=5,
                markerfacecolor='none',
                markeredgecolor=self.config.colors["chart_hover"],
                markeredgewidth=1.5,
                linestyle='',
                zorder=10
            )

            # 检查是否显示文本框
            if self.config.get("show_textbox", True):
                # 根据Max/Min位置确定Hover文本位置
                position = self.config.get("max_min_position")
                alpha = self.config.get("textbox_alpha")

                # 动态计算文本位置，避免重叠
                if position == "top-left":
                    hover_x, hover_y = 0.02, 0.75  # 调整Y位置，避免与Max/Min重叠
                    hover_ha, hover_va = 'left', 'top'
                elif position == "top-right":
                    hover_x, hover_y = 0.98, 0.75  # 调整Y位置，避免与Max/Min重叠
                    hover_ha, hover_va = 'right', 'top'
                elif position == "bottom-left":
                    hover_x, hover_y = 0.02, 0.25  # 调整Y位置，避免与Max/Min重叠
                    hover_ha, hover_va = 'left', 'bottom'
                elif position == "bottom-right":
                    hover_x, hover_y = 0.98, 0.25  # 调整Y位置，避免与Max/Min重叠
                    hover_ha, hover_va = 'right', 'bottom'

                # 更新左上角的标注文本
                hover_data_text = f'Hover: {nav:.4f} ({date.strftime("%y/%m/%d")})'

                # 修正: 统一Hover文本颜色为橙色
                self.hover_text_obj = self.app.ax.text(
                    hover_x, hover_y,
                    hover_data_text,
                    transform=self.app.ax.transAxes,
                    fontsize=8,
                    color=self.config.colors["chart_hover"],
                    bbox=dict(
                        boxstyle="round,pad=0.3",  # 减小内边距
                        fc="white",
                        ec="none",
                        lw=0,
                        alpha=alpha
                    ),
                    ha=hover_ha,
                    va=hover_va,
                    zorder=10
                )

            self.app.canvas.draw_idle()

        except Exception as e:
            self.on_leave(event)
            return

    def on_leave(self, event):
        """处理鼠标离开事件，移除标注和标记"""
        # 如果有设置的悬停日期，则不处理鼠标离开事件
        if self.config.get("show_hover_data") and self.config.get("hover_date"):
            return
            
        # 只移除悬停时创建的临时对象
        if self.hover_line_x:
            try:
                self.hover_line_x.remove()
            except:
                pass
            self.hover_line_x = None

        if self.hover_line_y:
            try:
                self.hover_line_y.remove()
            except:
                pass
            self.hover_line_y = None

        if self.hover_marker:
            try:
                self.hover_marker.remove()
            except:
                pass
            self.hover_marker = None

        if self.hover_text_obj:
            try:
                self.hover_text_obj.remove()
            except:
                pass
            self.hover_text_obj = None

        self.app.canvas.draw_idle()

    def update_chart_with_hover_date(self):
        """更新图表，显示悬停日期的交叉线"""
        if not self.config.get("show_hover_data") or not self.config.get("hover_date"):
            return

        try:
            hover_date = datetime.strptime(self.config.get("hover_date"), "%Y-%m-%d")
            if self.app.current_plot_data is not None:
                # 找到最接近的日期
                closest_idx = self.app.current_plot_data['日期'].sub(hover_date).abs().idxmin()
                closest_row = self.app.current_plot_data.loc[closest_idx]
                nav = closest_row['单位净值']
                date = closest_row['日期']

                # 清除之前的悬停标记
                self.remove_hover_date_marker()

                # 添加悬停十字线
                self.hover_date_marker_x = self.app.ax.axvline(
                    x=date,
                    color=self.config.colors["chart_hover"],
                    linestyle='--',
                    linewidth=1,
                    alpha=0.5,
                    zorder=5
                )

                self.hover_date_marker_y = self.app.ax.axhline(
                    y=nav,
                    color=self.config.colors["chart_hover"],
                    linestyle='--',
                    linewidth=1,
                    alpha=0.5,
                    zorder=5
                )

                # 添加空心圆标记
                self.hover_date_marker, = self.app.ax.plot(
                    date,
                    nav,
                    marker='o',
                    markersize=5,
                    markerfacecolor='none',
                    markeredgecolor=self.config.colors["chart_hover"],
                    markeredgewidth=1.5,
                    linestyle='',
                    zorder=10
                )

                self.app.canvas.draw_idle()
        except ValueError:
            self.app.log("悬停日期格式无效", "error")

    def remove_hover_date_marker(self):
        """清除悬停日期标记"""
        if hasattr(self, 'hover_date_marker_x') and self.hover_date_marker_x:
            try:
                self.hover_date_marker_x.remove()
            except:
                pass
            self.hover_date_marker_x = None

        if hasattr(self, 'hover_date_marker_y') and self.hover_date_marker_y:
            try:
                self.hover_date_marker_y.remove()
            except:
                pass
            self.hover_date_marker_y = None

        if hasattr(self, 'hover_date_marker') and self.hover_date_marker:
            try:
                self.hover_date_marker.remove()
            except:
                pass
            self.hover_date_marker = None

        self.app.canvas.draw_idle()