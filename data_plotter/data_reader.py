import os
from pathlib import Path
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from pandas import read_pickle
from sympy.core.numbers import NaN


class DataPlotter:
    def __init__(self, data_file):
        parentspath = data_file.parent
        self.figure_data = parentspath.name
        self.my_data = self.restore_raw_data(data_file)
        self.x_values = self.my_data['x']['run_1']
        self.data_monotonic = self.my_data['monotonic']['run_1']
        self.sma_x = self.x_values.rolling(100).mean()
        self.y_values = self.my_data['y']['run_1']
        self.sma_y = self.y_values.rolling(100).mean()
        self.n = int(len(self.x_values) * 0.008)

        self.real_data = pd.concat([self.x_values, self.y_values, self.data_monotonic], axis=1)
        ''' self.x_values.to_excel('x_values.xlsx')
        self.x_values.to_csv('x_values', index=True)
        self.y_values.to_csv('y_values', index=True)
        self.real_data.to_csv('real data values', index=True)
        self.real_data.to_excel('real_data_values.xlsx')'''

    def restore_raw_data(self, path: Path):
        """
            Read the dataframe from the specified path and returns it

            Args:
                path (Path): The path, file containing the dataframe.

            Return:
                read_pickle(path) :Load pickled pandas object from file
        """
        return read_pickle(path)


    def find_target_value(self):
        """
            Find the target values
            Return:
                target_x : Series containing the target x values.
        """
        target_x = self.sma_x[
            ((self.sma_x.shift(1) >= 0) & (self.sma_x < 0)) | ((self.sma_x.shift(1) <= 0) & (self.sma_x > 0))]
        return target_x

    def definition_distance(self):
        """
             Calculate the definition distance and return the corresponding error list.

            - Determines the indices where target values are found using the `find_target_value` method.
            - Calculates the definition distance and error for each pair of target indices.
            - Returns a list of errors corresponding to the definition distances.

            Returns:
                error_list: A list of errors (in percentage) for each definition distance.

        """
        idx_list = [0]
        for idx in self.find_target_value().index:
            idx_list.append(idx)
        idx_list.append(29788)
        result_list = []
        error_list = []
        for i in range(len(idx_list) - 1):
            idx = idx_list[i]
            next_idx = idx_list[i + 1]

            index_x_after = idx + self.n
            index_x_before = next_idx - self.n

            first_value_monotonic = self.my_data['monotonic'][index_x_after]
            first_value_x_plot = self.my_data['x_plot'][index_x_after]

            second_value_monotonic = self.my_data['monotonic'][index_x_before]
            second_value_x_plot = self.my_data['x_plot'][index_x_before]

            data_between_monotonic = self.my_data['monotonic'][index_x_after:index_x_before]
            data_between_x_plot = self.my_data['x_plot'][index_x_after:index_x_before]
            data_between_x = self.my_data['x'][index_x_after:index_x_before]

            data_concat = pd.concat((data_between_monotonic, data_between_x, data_between_x_plot), axis=1)
            time = abs(first_value_monotonic - second_value_monotonic)
            delta_x_sum = data_between_x.sum()

            therotical_distance = abs(delta_x_sum)
            pyschical_distance = (100 * time * 0.000001) / 0.03175
            error = abs(1 - (pyschical_distance / therotical_distance)) * 100
            error_list.append(error)
            result = (time - 1) * 0.03175
            result_list.append(f'{i}-) {result}')

        return error_list

    def find_corner_value(self):
        """
            Find the corner values of cumulative path and filter the corner according that values

            Return:
                  filtered_data_clean: The filtered real data after applying the corner value filtering.
            Notes:
                - The corner values are determined based on the changes in the 'sma_x' column.
                - The filtering is applied by removing data points in a window around the identified corner values.
                - The first 200 and last 200 data points are also set to NaN.
        """

        real_data_update = self.real_data
        self.find_target_value().index = self.find_target_value().index - 50

        for idx in self.find_target_value().index:
            real_data_update.iloc[(idx - self.n): (idx + self.n)] = NaN
        real_data_update.iloc[0: 200] = NaN
        real_data_update.iloc[len(real_data_update) - 200:] = NaN
        filtered_data_clean = abs(real_data_update.dropna())

        return filtered_data_clean

    def detect_jump_x(self):
        """
            Detect the jumped values of x series and pass the csv file
        :return: None
        """
        jump_value = self.find_corner_value()['x'].diff()
        filtered_jump_value_x = jump_value[abs(jump_value) > 10]
        print(filtered_jump_value_x)
        filtered_jump_value_x.to_csv('detect value of x', index=True)

    def cumulative_path(self):
        """
            According to the mean value of x(sma_x) and y(sma_y) calculate the cumulative path

        """
        plt.subplot(3, 2, 1)
        plt.title('cumulative path')
        cum_sma_x = np.cumsum(self.sma_x)
        cum_sma_y = np.cumsum(self.sma_y)
        plt.plot(cum_sma_x, cum_sma_y)

    def delta_x_features(self):
        """
            Calculate and visualize the features related to delta x values

            Notes:
            -Calculates the difference between consecutive x values
            -Finds the minimum, maximum and average of filtered delta x values.
            -Plots a histogram of delta x values and adds annotations for min, max, median and average.

        """
        plt.subplot(3, 2, 2)
        plt.title('Delta X')
        delta_x = self.find_corner_value()['x'].diff()
        delta_x_filtered = delta_x[np.isfinite(delta_x)]  # remove the NaN
        delta_x_min = min(delta_x_filtered)
        delta_x_max = max(delta_x_filtered)
        delta_x_filtered.to_excel('delta_x.xlsx')
        delta_x_med = delta_x_filtered.median()
        delta_x_avrg = delta_x_filtered.mean()
        hist_values, bin_edges, _ = plt.hist(delta_x, bins=500)

        plt.text(delta_x_min, max(hist_values), f"Min: {delta_x_min:.1f}", va='top', ha='left', color='red')
        plt.text(delta_x_max, max(hist_values), f"Max: {delta_x_max:.1f}", va='top', ha='right', color='red')
        plt.text(delta_x_med, max(hist_values), f"Median: {delta_x_med:.2f}", va='top', ha='center', color='red')
        plt.text(delta_x_avrg, max(hist_values) * 0.9, f"Average: {delta_x_avrg:.5f}", va='top', ha='center',
                 color='blue')

    def report_rate(self):
        """
            Calculate and visualize the report rate based on monotonic data

            Notes :
            -Retrieves the monotonic data from the corner values.
            -Plots a histogram of the difference values within the range of 500 to 1500.
        """
        plt.subplot(3, 2, 3)
        data_monotonic = self.find_corner_value()['monotonic']
        data_diff_monotonic = data_monotonic.diff()
        plt.title('Report Rate')
        plt.hist(data_diff_monotonic, range=[500, 1500], bins=500)

    def filtering_corner(self):
        """
            Perform filtering corner calculations and visualize the cumulative sum of x and y values.
            Calculate the cumulative sum of absolute x and y values.

            Return :
                plot : The plot object representing the cumulative sum curve.

        """
        plt.subplot(3, 2, 4)
        plt.title('filtering corner')
        cumulative_sum_x = np.cumsum(abs(self.find_corner_value()['x']))
        cumulative_sum_y = np.cumsum(abs(self.find_corner_value()['y']))

        return plt.plot(cumulative_sum_x, cumulative_sum_y, linewidth=1.0)

    def display_error(self):
        """
            Display the report error as a bar plot and table.
            Retrieves the error values from the definition distance.
            Creates a bar plot to visualize the error values.

        :return: None
        """

        plt.subplot(3, 2, 5)
        data_error = np.array(self.definition_distance())
        columns = range(10)
        rows = range(1)
        index = np.arange(len(columns)) + 0.5
        bar_width = 0.4
        cell_text = []
        plt.bar(index, data_error, bar_width, 0)
        cell_text.append(['%0.1f' % row for row in self.definition_distance()])
        the_table = plt.table(cellText=cell_text,
                              rowLabels=rows,
                              colLabels=columns,
                              loc='bottom'
                              )
        plt.title('Report Error')
        plt.xticks([])

    def plot_data(self):
        """
            Plot the all functions and shows the plot.

        """
        plt.figure(self.figure_data)
        self.cumulative_path()
        self.filtering_corner()
        self.report_rate()
        self.delta_x_features()
        self.detect_jump_x()
        self.definition_distance()
        self.display_error()
        plt.subplots_adjust(wspace=0.5, hspace=0.5)
        plt.show()


DATA_FILE = Path(r'C:\Users\User\PycharmProjects\LogitechProjects\data_plotter\Footloose\Footloose\FootLosse_800DPI_CrushFlat_100mms')
plotter = DataPlotter(DATA_FILE)
plotter.plot_data()
