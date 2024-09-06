import pickle
from pathlib import Path
import numpy
import numpy as np
from scipy.stats import zscore
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sb


def restore_data():
    file_path = Path(f'raw_data/raw_data.bin')

    with open(file_path, 'rb') as outfile:
        data = pickle.load(outfile)

        for dpi, dpi_infos in data['data'].items():
            for angle, angle_info in dpi_infos.items():
                for idx, speed_info in enumerate(angle_info):
                    speed = speed_info[0]
                    points = speed_info[1]
                    df = DataFrame(points, columns=['Monotonic', 'X', 'Y'])
                    df['delta'] = df['Monotonic'] - df['Monotonic'].shift()
                    data['data'][dpi][angle][idx][1] = df

        return data['test_params'], data['data']


def standart_deviation():
    params, data = restore_data()

    test_data = data[(1000,)][0][20][1]
    filtered_data_frame = test_data['delta'][test_data['delta'].notnull()]
    z_scores = zscore(filtered_data_frame)
    count, hist = numpy.histogram(z_scores, bins=8, range=(-4, 4))

    total_points = np.sum(count)
    percentage_values = count / total_points * 100
    rounded_array = np.round(percentage_values, decimals=1)

    # Visualizing the distribution
    plt.subplot(1, 2, 1)
    sb.set_style('whitegrid')
    plt.stairs(rounded_array, hist, fill=True)
    plt.xlabel('std')

    # display pie

    rounded_array_reverse = rounded_array[::-1]
    result_sum = rounded_array + rounded_array_reverse

    result_pie = result_sum[:4]
    result_pie_rounded = np.round(result_pie, decimals=1)
    range_list = ['(-4σ,-3σ)-(3σ,4σ)', '(-3σ,-2σ)-(2σ,3σ)', '(-2σ,-1σ)-(1σ,2σ)', '(-1σ ,-0)-(0,1σ)']
    # pie_text = [f"{value}%-" for value in result_pie_rounded]

    plt.subplot(1, 2, 2)
    wedges, texts, autotexts = plt.pie(result_pie_rounded, autopct='%1.1f%%')

    plt.legend(wedges, range_list,
               title="percentage of std",
               loc="center left",
               bbox_to_anchor=(0.9, 0, 0.5, 1))
    plt.xlabel('percentage in pie')

    # plt.ylabel('Probability Density')
    plt.show()


def demo_polling_rate():
    params, data = restore_data()

    test_data = data[(1000,)][45][20][1]

    fig, ax = plt.subplots()
    filtered_delta = test_data['delta'][test_data['delta'].notnull()].values
    ax.hist(filtered_delta, bins='auto')
    plt.show()

    return filtered_delta


# demo_polling_rate()
standart_deviation()
