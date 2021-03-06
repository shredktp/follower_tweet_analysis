from __future__ import print_function
from datetime import datetime
from numpy import *

import operator
import fileinput

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy.stats import norm
import numpy as np
from sklearn.neighbors.kde import KernelDensity


def process_data(source_path_param, output, choice):
    for line in fileinput.input([source_path_param], openhook=fileinput.hook_encoded("utf8")):
        value = line.split(',')
        # print(value)
        x = int(value[12].strip())  # hour
        y = 0.0
        if choice == 'retweet':
            y = float(value[3].strip())  # diff_retweet
        elif choice == 'follower_wt_mc':
            y = float(value[10].strip())  # diff_follower_wt_mc
        elif choice == 'follower_wo_mc':
            y = float(value[13].strip())  # diff_follower_wo_mc
        output[x].append(y)
    fileinput.close()
    return


def estimate(input_param, output, hour):
    if not input_param:
        nothing_message = "Nothing at t: " + str(hour)
        # print(nothing_message)
        output.append(0.0)
    elif len(input_param) == 1:
        nothing_message = "Only One Source Tweet at t: " + str(hour)
        # print(nothing_message)
        output.append(0.0)
    else:
        # print("Round :" + str(hour))
        # print("input_param:  " + str(input_param))
        x = array(input_param)
        # print("Array x: " + str(x))
        try:
            kde = stats.gaussian_kde(x)
        except np.linalg.linalg.LinAlgError:
            # print("Singular Matrix at t: " + str(hour))
            output.append(0.0)
            return
        xs = linspace(min(input_param), max(input_param), num=100)
        kde.set_bandwidth(bw_method='silverman')
        kde.set_bandwidth(bw_method=kde.factor / 2)
        y = kde(xs)
        sum_weight = 0
        value = 0
        for j in range(0, len(xs)):
            value += xs[j]*y[j]
            sum_weight += y[j]

        avg = value/sum_weight
        output.append(avg)
    return

def plot_kde(data_estimate_param, choose_str, topic_name, fold_num):
    # print("dfgjhjtrter")
    fig, ax = plt.subplots()
    ax.plot(range(0, len(data_estimate_param)), data_estimate_param, label='KDE')
    if topic_name == 'apple' or topic_name == 'aroii':
        ax.set_xlabel("Time(Hour) from 17-Nov-2015 06:00 am")
    elif topic_name == 'hormonestheseries' or topic_name == 'thefacethailand':
        ax.set_xlabel("Time(Hour) from 09-Nov-2015 06:00 am")

    if choose_str == 'follower_wt_mc':
        ax.set_ylabel('Delta Follower with Message Count')
        ax.set_title('Graph of Time and Delta Follower(with Message Count) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
    elif choose_str == 'follower_wo_mc':
        ax.set_ylabel('Delta Follower without Message Count')
        ax.set_title('Graph of Time and Delta Follower(without Message Count) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
    elif choose_str == 'retweet':
        ax.set_ylabel('Delta Retweet')
        ax.set_title('Graph of Time and Delta Retweet [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
    axes = plt.gca()
    axes.set_xlim([0, len(data_estimate_param)])
    plt.show()
    return


def write_date_date_csv(output_path, list_data, start_unix_time, topic_name):
    # print(list_data)
    before_start_time = 0
    one_hour = 3600

    if each_topic == "hormonestheseries" or each_topic == "thefacethailand":
        before_start_time = start_unix_time[0] - one_hour
    elif each_topic == "apple" or each_topic == "aroii":
        before_start_time = start_unix_time[1] - one_hour
    unix_time = before_start_time
    t = 1

    fo = open(output_path, "w")
    for line in list_data:
        if unix_time != before_start_time:
            date_time_str = datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')
            if line == 0.0:
                result = str(date_time_str) + ",NA\n"
                # result = str(t) + " " + str(date_time_str) + ",NA\n"  # TEST
            else:
                result = str(date_time_str) + "," + str(line) + "\n"
                # result = str(t) + " " + str(date_time_str) + "," + str(line) + "\n"  # TEST
            # print(result)  # TEST
            t += 1
            fo.write(result)
        unix_time += one_hour

    fo.close()
    return


def decompose_time_series_plot(data_path, topic_name, fold_num, is_plot_decompose_param, is_plot_observed_param):

    kde_follower = pd.read_csv(data_path,
                              names=['DateTime', 'DeltaFollower'],
                              index_col=['DateTime'],
                              parse_dates=True)

    decomp_freq = int(18*7)
    # decomp_freq = int(1)
    kde_follower_interpolated_bfill = kde_follower.DeltaFollower.interpolate().bfill()

    """
    # Test Write To CSV File
    # output_path_non_interpolate = "E:/tweet_process/result_follower-ret/092_cmp_interpolate_and_bfill/" + topic_name + "/fold_" + fold_num + "/01_original_data.csv"
    # output_path_interpolate = "E:/tweet_process/result_follower-ret/092_cmp_interpolate_and_bfill/" + topic_name + "/fold_" + fold_num + "/02_original_interpolate.csv"
    # output_path_interpolate_bfill = "E:/tweet_process/result_follower-ret/092_cmp_interpolate_and_bfill/" + topic_name + "/fold_" + fold_num + "/03_bfill_interpolate.csv"
    # kde_follower.DeltaFollower.to_csv(output_path_non_interpolate, sep='\t')
    # kde_follower_interpolated_forward.to_csv(output_path_interpolate, sep='\t')
    # kde_follower_interpolated_bfill.to_csv(output_path_interpolate_bfill, sep='\t')
    # print("Original - Forward ->  " + str(kde_follower.DeltaFollower.equals(kde_follower_interpolated_forward)))
    # print("Forward - OnlyBfill -> " + str(kde_follower_interpolated_forward.equals(kde_follower_interpolated_bfill)))
    """
    res_only_bfill = sm.tsa.seasonal_decompose(kde_follower_interpolated_bfill.values,
                                               freq=decomp_freq,
                                               model='additive')

    # SELECT GRAPH PLOT
    # 1 not Interpolate Plot
    # ori_plot = kde_follower.DeltaFollower.plot()
    # ori_plot.set_title("Topic: " + str(topic_name) + " Fold: " + str(fold_num))
    # 2 Interpolate Plot
    if is_plot_observed_param:
        ori_interpolated_plot = kde_follower.DeltaFollower.interpolate().plot()
        ori_interpolated_plot.set_ylabel("Delta Retweet (KDE)")
        ori_interpolated_plot.set_title("Observed of Delta Retweet (KDE) (Topic: " + str(topic_name) + " Fold: " + str(fold_num) + ")")
        # plt.title('Observed of Delta Follower) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
        plt.show()
    # 3 Decomposition Plot
    if is_plot_decompose_param:
        res_plot = res_only_bfill.plot()
        # plt.title('Decomposition of Delta Retweet) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
        plt.show()

    # print(res_only_bfill.trend)
    # print(res_only_bfill)

    return kde_follower_interpolated_bfill, res_only_bfill


def plot_diff_ret_and_diff_fol(list_ret, list_fol, choose_str, topic_name, fold_num, is_log_delta_retweet_param, is_log_delta_follower_param, is_limit_axis_param, max_fol, max_ret, min_fol, min_ret):
    plt.plot(list_ret, list_fol, 'ro')
    if is_limit_axis_param:
        plt.axis([min_ret, max_ret, min_fol, max_fol])
    else:
        plt.axis([min(list_ret), max(list_ret), min(list_fol), max(list_fol)])
    # plt.axis('tight')
    if is_log_delta_retweet_param and is_log_delta_follower_param:
        plt.xlabel('Log(Delta Retweet)')
        if choose_str == 'follower w/t mc':
            plt.ylabel('Log(Delta Follower with Message Count)')
            plt.title('Graph of Log(Delta Retweet) and Log(Delta Follower(with Message Count)) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
        elif choose_str == 'follower w/o mc':
            plt.ylabel('Log(Delta Follower without Message Count)')
            plt.title('Graph of Log(Delta Retweet) and Log(Delta Follower(without Message Count)) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')

    elif is_log_delta_retweet_param:
        plt.xlabel('Log(Delta Retweet)')
        if choose_str == 'follower w/t mc':
            plt.ylabel('Delta Follower with Message Count')
            plt.title('Graph of Log(Delta Retweet) and Delta Follower(with Message Count) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
        elif choose_str == 'follower w/o mc':
            plt.ylabel('Delta Follower without Message Count')
            plt.title('Graph of Log(Delta Retweet) and Delta Follower(without Message Count) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')

    elif is_log_delta_follower_param:
        plt.xlabel('Delta Retweet')
        if choose_str == 'follower w/t mc':
            plt.ylabel('Log(Delta Follower with Message Count)')
            plt.title('Graph of Delta Retweet and Log(Delta Follower(with Message Count)) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
        elif choose_str == 'follower w/o mc':
            plt.ylabel('Log(Delta Follower without Message Count)')
            plt.title('Graph of Delta Retweet and Log(Delta Follower(without Message Count)) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')

    else:
        plt.xlabel('Delta Retweet')
        if choose_str == 'follower w/t mc':
            plt.ylabel('Delta Follower with Message Count')
            plt.title('Graph of Delta Retweet and Delta Follower(with Message Count) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
        elif choose_str == 'follower w/o mc':
            plt.ylabel('Delta Follower without Message Count')
            plt.title('Graph of Delta Retweet and Delta Follower(without Message Count) [Topic: ' + topic_name + ', Fold: ' + fold_num + ']')
    plt.show()


def stats_gaussian_kde_plot(dataframe):
    kde = stats.gaussian_kde(dataframe.values)
    xs = np.linspace(-10, 10, num=50)
    y1 = kde(xs)
    print(kde.factor)
    kde.set_bandwidth(bw_method='silverman')
    y2 = kde(xs)
    print(kde.factor)
    kde.set_bandwidth(bw_method=kde.factor / 3)  # 100 - 1000
    # kde.set_bandwidth(bw_method=)
    y3 = kde(xs)
    print(kde.factor)

    fig, ax = plt.subplots()
    ax.plot(dataframe.values, np.ones(dataframe.values.shape) / (4. * dataframe.values.size), 'bo', label='Data points (rescaled)')
    # ax.plot(xs, y1, label='Scott (default)')
    # ax.plot(xs, y2, label='Silverman')
    ax.plot(xs, y3, label='Const (1/3 * Silverman)')
    ax.legend()
    plt.show()
    # print(min(df_kde_value.values))
    # print(df_kde_value.shape)
    # print(df_kde_value.values.size)


def sklearn_kde_plot(dataframe, choose_choice, topic_name, fold_num):
    # print(dataframe)
    N = dataframe.values.size
    X = dataframe.values[:, np.newaxis]

    # X_plot = np.linspace(min(dataframe.values), max(dataframe.values), num=500)[:, np.newaxis]
    X_plot = np.linspace(min(dataframe.values), 10, num=500)[:, np.newaxis]                                     # SET THISS
    # X_plot = np.linspace(min(dataframe.values), 10, num=500)[:, np.newaxis]
    # print(min(dataframe.values))
    # print(max(dataframe.values))
    # print(dataframe)

    true_dens = (0.3 * norm(0, 1).pdf(X_plot[:, 0]) + 0.7 * norm(5, 1).pdf(X_plot[:, 0]))
    fig, ax = plt.subplots()
    # ax.fill(X_plot, true_dens, fc='black', alpha=0.2, label='input distribution')

    # kde = KernelDensity(kernel='gaussian', bandwidth=0.005).fit(X)  # 'tophat', 'epanechnikov'
    kde = KernelDensity(kernel='gaussian', bandwidth=0.01).fit(X)  # 'tophat', 'epanechnikov'              SET THISSSSSSSS
    log_dens = kde.score_samples(X_plot)
    ax.plot(X_plot[:, 0], np.exp(log_dens), '-', label="kernel = '{0}'".format('gaussian'))

    ax.text(6, 0.38, "N={0} points".format(N))
    ax.legend(loc='upper right')
    # ax.plot(X[:, 0], -0.005 - 0.0005 * np.random.random(X.shape[0]), '+k')
    ax.plot(X[:, 0], -0.005 - 0.005 * np.random.random(X.shape[0]), '+k')

    # ax.set_xlim(min(dataframe.values), max(dataframe.values))
    ax.set_xlim(0, 10)                                                                                      # SET THISSSSSSSS
    # ax.set_ylim(-0.02, 1)
    ax.set_ylim(-0.02, 1.0)                                                                                 # SET THISSSSSSSS
    ax.set_xlabel("Delta Follower")
    ax.set_ylabel("Density")
    plt.title('Density - ' + choose_choice + ' (' + topic_name + ', ' + fold_num + ')')
    plt.show()
    return


# y_axis_choices = ['retweet', 'follower_wt_mc', 'follower_wo_mc']
# y_axis_choices = ['retweet', 'follower_wo_mc']
# y_axis_choices = ['follower_wo_mc']
y_axis_choices = ['retweet']
topics = ["apple", "aroii", "hormonestheseries", "thefacethailand"]
# folds = ["1", "2", "3", "4", "5"]
folds = ["1"]

unix_time_start = [1447023600, 1447714800]  # 2015-11-09 06:00:00   2015-11-17 06:00:00
last_hour_app_aroii = 1651
last_hour_hor_theface = 1627

is_plot_kde = False
is_plot_decompose = False
is_plot_observed = True
is_plot_sklearn_kde = False

is_write_decomposed_trend = False
is_write_date_time_kde_value = False

for each_choice in y_axis_choices:
    for each_topic in topics:
        for each_fold in folds:

            print("============ Topic: " + each_topic + ", Fold: " + each_fold + ", " + each_choice + " =============")
            data = []  # Array for collect original data
            data_estimate = []  # Array for collect KDE processed data

            source_path = "E:/tweet_process/result_follower-ret/06_diff_ret_fol_result/" + each_topic + "/fold_" + each_fold + "/all_tweet.csv"
            # source_path = "E:/tweet_process/result_follower-ret/06_diff_ret_fol_result/aroii/fold_1/t1.csv"
            output_follower_csv = "E:/tweet_process/result_follower-ret/07_follower_csv/" + each_topic + "/date_" + each_choice + "_" + each_fold + ".csv"
            output_retweet_csv = "E:/tweet_process/result_follower-ret/08_retweet_csv/" + each_topic + "/date_" + each_choice + "_" + each_fold + ".csv"
            output_decomposition = "E:/tweet_process/result_follower-ret/11_trend_decomposed/" + each_topic + "/decomposition_" + each_fold + "_" + each_choice + ".csv"

            """
            Initial List
            """
            if each_topic == "apple" or each_topic == "aroii":
                for i in range(0, last_hour_app_aroii):
                    data.append([])
            else:
                for i in range(0, last_hour_hor_theface):
                    data.append([])

            """
            Read data from file (06_diff_ret_fol_result) and collect in array
            (Select 'Retweet', 'Follower' by y_axis_choices parameter)
            """
            process_data(source_path, data, each_choice)
            # print(data)

            """
            KDE processing
            """
            for i in range(0, len(data)):
                estimate(data[i], data_estimate, i)
            # print(len(data_estimate))
            # print(data_estimate)

            # for i in range(0, len(data_estimate)):
            #     # if data_estimate[i] > 7:
            #     #     print(str(i) + ": " + str(data_estimate[i]))
            #     if data_estimate[i] > 1:
            #         print(str(i) + ": " + str(data_estimate[i]))
            # # print(data_estimate[0])

            """
            Plot KDE_interpolated(Delta_Retweet or Delta_Follower) - Time(Hours)
            """
            # print(data_estimate)
            if is_plot_kde:
                plot_kde(data_estimate, each_choice, each_topic, each_fold)

            """
            !!!!! Write Data !!!!!
            """
            if is_write_date_time_kde_value:
                if each_choice == 'follower_wo_mc':
                    write_date_date_csv(output_follower_csv, data_estimate, unix_time_start, each_topic)
                elif each_choice == 'retweet':
                    write_date_date_csv(output_retweet_csv, data_estimate, unix_time_start, each_topic)

            """
            Plot Y-Time Graph (Pandas)
            """
            if each_choice == 'follower_wo_mc':
                df_kde_value, decomposed_value = decompose_time_series_plot(output_follower_csv, each_topic, each_fold, is_plot_decompose, is_plot_observed)  # Date Time,Follower_count
            # elif each_choice == 'retweet':
            else:  # This can be 'retweet', 'follower_wt_mc'
                df_kde_value, decomposed_value = decompose_time_series_plot(output_retweet_csv, each_topic, each_fold, is_plot_decompose, is_plot_observed)  # Date Time,Retweet_count
            # print(df_kde_value)

            """
            !!!!! Write Data Trend from Decomposition !!!!!
            """
            if is_write_decomposed_trend:
                decomposed_value.trend.tofile(output_decomposition, sep='\n')
            # print(decomposed_value.trend)

            """
            KDE Plot 1 (sklearn.neighbors.kde) OK
            """
            if is_plot_sklearn_kde:
                sklearn_kde_plot(df_kde_value, each_choice, each_topic, each_fold)
            # print(df_kde_value)

            # ================================ Unused =====================================
            # """
            # Print TOP KDE delta_follower (Find Events) (Unused)
            # """
            # dict_max = {}
            # for k in range(1, len(df_kde_value)):
            #     dict_max[str(k)] = df_kde_value.values[k]
            # sorted_x = sorted(dict_max.items(), key=operator.itemgetter(1))
            # sorted_x.reverse()
            # print(len(sorted_x))
            # print(sorted_x[:10])

            # """
            # KDE Plot 2 (scipy.stats) (Unused)
            # """
            # stats_gaussian_kde_plot(df_kde_value)
