# core.py
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import warnings
import re
from dateutil.parser import parse as dateutil_parse
from utils import log_message, parse_dates, clean_numeric_string

class PerformanceAnalysis:
    def __init__(self, df, log_callback=None):
        self.df = df
        self.log = log_callback if log_callback else log_message

    def prepare_data(self):
        """清洗和准备数据，包括日期和净值列的转换，并处理多样的列名"""
        if self.df is None or self.df.empty:
            self.log("数据为空，无法进行分析。", "warning")
            return self.df
        
        # 定义可能的列名映射
        column_map = {
            '日期': ['日期', '净值日期', 'Date', 'date', '交易日期'],
            '单位净值': ['单位净值', '净值', '累计净值', '单位净值(元)', 'NAV']
        }

        # 尝试匹配并重命名日期列
        found_date_col = False
        for potential_name in column_map['日期']:
            if potential_name in self.df.columns:
                if potential_name != '日期':
                    self.df.rename(columns={potential_name: '日期'}, inplace=True)
                    self.log(f"已将列 '{potential_name}' 重命名为 '日期'。", "info")
                found_date_col = True
                break
        
        if not found_date_col or '日期' not in self.df.columns:
            self.log("未找到有效的日期列，请确保文件包含日期信息。", "error")
            return None
        
        # 尝试匹配并重命名单位净值列
        found_nav_col = False
        for potential_name in column_map['单位净值']:
            if potential_name in self.df.columns:
                if potential_name != '单位净值':
                    self.df.rename(columns={potential_name: '单位净值'}, inplace=True)
                    self.log(f"已将列 '{potential_name}' 重命名为 '单位净值'。", "info")
                found_nav_col = True
                break
        
        if not found_nav_col or '单位净值' not in self.df.columns:
            self.log("未找到有效的单位净值列，请确保文件包含净值信息。", "error")
            return None
        
        self.log("开始解析日期列...", "info")
        self.df['日期'] = self.df['日期'].astype(str)
        
        # 使用更强大的日期解析函数
        self.df['日期'] = parse_dates(self.df['日期'], self.log)
        
        invalid_mask = self.df['日期'].isna()
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            self.log(f"发现 {invalid_count} 行日期格式无效", "warning")
            self.df = self.df[~invalid_mask]
            self.log(f"已删除 {invalid_count} 行无效日期数据", "info")
        
        if len(self.df) == 0:
            return None
        
        if len(self.df) > 1:
            first_date = self.df['日期'].iloc[0]
            last_date = self.df['日期'].iloc[-1]
            if first_date > last_date:
                self.log("日期顺序不正确，正在反转数据...", "warning")
                self.df = self.df.iloc[::-1].reset_index(drop=True)
        
        self.log("开始处理单位净值列...", "info")
        
        # 使用 apply 方法并行处理，并清理非数值字符
        self.df['单位净值'] = self.df['单位净值'].apply(clean_numeric_string)
        
        # 批量转换为 float 类型，使用 errors='coerce' 将无法转换的值设为 NaN
        self.df['单位净值'] = pd.to_numeric(self.df['单位净值'], errors='coerce')
        
        invalid_nav_mask = self.df['单位净值'].isna()
        invalid_nav_count = invalid_nav_mask.sum()
        
        if invalid_nav_count > 0:
            self.log(f"发现 {invalid_nav_count} 行单位净值无效", "warning")
            self.df = self.df[~invalid_nav_mask]
            self.log(f"已删除 {invalid_nav_count} 行无效单位净值数据", "info")
            
        if len(self.df) == 0:
            self.log("数据清洗后为空", "error")
            return None
            
        return self.df

    def calculate_annual_return(self, nav_start, nav_end, days):
        """计算年化收益率"""
        if days == 0:
            return 0.0
        
        total_return = (nav_end - nav_start) / nav_start
        if total_return <= -1.0:
            # 避免 log(0) 或 log(负数)
            return -1.0  
        annual_return = (1 + total_return) ** (365.0 / days) - 1
        return annual_return
        
    def calculate_max_drawdown(self, nav_series):
        """计算最大回撤"""
        if nav_series.empty:
            return 0.0
        
        # 使用 cummax() 计算截至当前日期的历史最高净值
        rolling_max = nav_series.cummax()
        # 计算回撤
        drawdown = (rolling_max - nav_series) / rolling_max
        # 找到最大回撤
        max_drawdown = drawdown.max()
        return max_drawdown

    def calculate_fixed_freq(self):
        """计算固定周期的业绩指标"""
        if self.df is None or len(self.df) == 0:
            self.log("数据为空，无法进行固定周期回测", "warning")
            return []
        
        first_date = self.df['日期'].iloc[0]
        last_date = self.df['日期'].iloc[-1]
        
        results = []
        
        # 新增：直接计算总天数，避免重复计算
        total_days = (last_date - first_date).days
        
        # 更新为按月和年划分的固定周期
        # 使用近似天数
        frequencies = {
            "近1周": 7,
            "近2周": 14,
            "近3周": 21,
            "近1月": 30,
            "近2月": 60,
            "近3月": 90,
            "近6月": 180,
            "近1年": 365,
        }

        for freq_name, days_ago in frequencies.items():
            start_date_target = last_date - timedelta(days=days_ago)
            
            # 使用 searchsorted 查找最接近起始日期的索引
            start_idx = self.df['日期'].searchsorted(start_date_target)
            
            # 确保找到的索引有效
            if start_idx >= len(self.df):
                start_idx = len(self.df) - 1
            if start_idx > 0 and (self.df['日期'].iloc[start_idx] - start_date_target).days > (start_date_target - self.df['日期'].iloc[start_idx-1]).days:
                start_idx -= 1
            
            sub_df = self.df.iloc[start_idx:].copy()
            
            # 方案二：基于数据点数量而不是天数来判断
            if len(sub_df) >= 2:
                days_actual = (sub_df['日期'].iloc[-1] - sub_df['日期'].iloc[0]).days
                
                # 检查实际天数是否达到指标天数的90%
                if days_actual < days_ago * 0.9:
                    # 不足90%，显示为占位符
                    results.append((freq_name, '/', '/', '/'))
                    self.log(f"数据不足{freq_name}的90%，跳过计算。实际天数: {days_actual}, 要求天数: {days_ago}", "warning")
                else:
                    nav_start = sub_df['单位净值'].iloc[0]
                    nav_end = sub_df['单位净值'].iloc[-1]
                    
                    annual_return = self.calculate_annual_return(nav_start, nav_end, days_actual)
                    max_drawdown = self.calculate_max_drawdown(sub_df['单位净值'])
                    
                    results.append((freq_name, days_actual, f"{annual_return:.2%}", f"-{max_drawdown:.2%}"))
                    self.log(f"{freq_name}: 天数={days_actual}, 年化={annual_return:.2%}, 回撤={max_drawdown:.2%}", "info")
            else:
                self.log(f"数据不足{freq_name}，跳过计算。实际数据点数: {len(sub_df)}", "warning")
                # 即使数据不足，也显示该周期，并用斜杠填充数据
                results.append((freq_name, '/', '/', '/'))

        # 计算成立以来
        if total_days > 0 and len(self.df) > 1:
            nav_start = self.df['单位净值'].iloc[0]
            nav_end = self.df['单位净值'].iloc[-1]
            annual_return = self.calculate_annual_return(nav_start, nav_end, total_days)
            max_drawdown = self.calculate_max_drawdown(self.df['单位净值'])
            
            results.append(("成立以来", total_days, f"{annual_return:.2%}", f"-{max_drawdown:.2%}"))
        else:
            self.log("数据不足，无法计算成立以来业绩", "warning")
            results.append(("成立以来", '/', '/', '/'))
        
        return results

    def calculate_custom_range(self, start_date, end_date):
        """计算自定义日期区间的业绩指标"""
        df_sorted = self.df.sort_values('日期').reset_index(drop=True)
        
        start_idx = df_sorted['日期'].searchsorted(start_date, side='left')
        end_idx = df_sorted['日期'].searchsorted(end_date, side='right') - 1
        
        if start_idx >= len(df_sorted) or start_idx > end_idx:
            self.log("指定日期范围超出数据范围", "warning")
            return None
            
        if end_idx < 0:
            end_idx = len(df_sorted) - 1
            
        actual_start_date = df_sorted['日期'].iloc[start_idx]
        actual_end_date = df_sorted['日期'].iloc[end_idx]
        
        days = (actual_end_date - actual_start_date).days
        
        if days <= 1:
            self.log("指定日期范围内天数不足，无法计算", "warning")
            return None
        
        nav_start = df_sorted['单位净值'].iloc[start_idx]
        nav_end = df_sorted['单位净值'].iloc[end_idx]
        
        annual_return = self.calculate_annual_return(nav_start, nav_end, days)
        
        nav_series = df_sorted.loc[start_idx:end_idx, '单位净值'].reset_index(drop=True)
        max_drawdown = self.calculate_max_drawdown(nav_series)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'days': days,
            'nav_start': nav_start,
            'nav_end': nav_end,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'actual_start_date': actual_start_date,
            'actual_end_date': actual_end_date
        }

    def prepare_chart_data(self, start_date=None, end_date=None):
        """为图表准备数据和标题"""
        df_plot = self.df.copy()
        
        if start_date and end_date:
            mask = (df_plot['日期'] >= start_date) & (df_plot['日期'] <= end_date)
            df_plot = df_plot.loc[mask]
            start_str = start_date.strftime("%Y/%m/%d")
            end_str = end_date.strftime("%Y/%m/%d")
            chart_title = f"{start_str}~{end_str}趋势图"
            current_start_date = start_date
            current_end_date = end_date
        else:
            start_date = df_plot['日期'].min()
            end_date = df_plot['日期'].max()
            start_str = start_date.strftime("%Y/%m/%d")
            end_str = end_date.strftime("%Y/%m/%d")
            chart_title = f"{start_str}~{end_str}净值趋势图"
            current_start_date = start_date
            current_end_date = end_date
        
        return df_plot, chart_title, current_start_date, current_end_date