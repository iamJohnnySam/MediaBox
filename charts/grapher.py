from datetime import datetime, timedelta

from matplotlib import image
from matplotlib import pyplot as plt

import logger


def convert_to_time(val):
    format_string = "%H:%M:%S"
    x = datetime.strptime(val, format_string)
    x = x.replace(second=0, microsecond=0, minute=0, hour=x.hour) + timedelta(hours=x.minute // 30)
    return x


def convert_to_date(val):
    format_string = "%Y/%m/%d"
    x = datetime.strptime(val, format_string)
    return x


def extractor(x_column, categories, y_column, convert_time=False):
    data = {}
    total_data = {}

    x_column_values = []
    for x in x_column:
        if x not in x_column_values:
            if convert_time:
                x_column_values.append(convert_to_time(x))
            else:
                x_column_values.append(x)

    i = 0
    for cat in categories:
        if cat not in data.keys():
            data[cat] = {}
            for x_column_value in x_column_values:
                data[cat][x_column_value] = 0

        if convert_time:
            x = convert_to_time(x_column[i])
        else:
            x = x_column[i]
        data[cat][x] = data[cat][x] + float(y_column[i])

        if x_column[i] in total_data.keys():
            total_data[x] = total_data[x] + float(y_column[i])
        else:
            total_data[x] = float(y_column[i])
        i = i + 1

    return data, total_data


def grapher_category(graph_list, x_name, y_name, chart_title):
    colors = ['b', 'g', 'r', 'c', 'm', 'y']
    color_val = 0

    if graph_list is None:
        return

    x_column = [row[0] for row in graph_list]
    categories = [row[1] for row in graph_list]
    y_column = [row[2] for row in graph_list]
    data, total_data = extractor(x_column, categories, y_column)

    fig1 = plt.figure()
    fig1.set_figwidth(10)
    fig1.set_figheight(5)

    prev_bar = None

    for cat in data.keys():
        plt.bar(list(data[cat].keys()), list(data[cat].values()), color=colors[color_val], label=cat, bottom=prev_bar)
        prev_bar = list(data[cat].values())

        color_val = color_val + 1
        if color_val == len(colors):
            color_val = 0

    plt.plot(list(total_data.keys()), list(total_data.values()), color=colors[color_val], label="Total")

    for i in range(len(total_data.keys())):
        plt.text(i, list(total_data.values())[i], list(total_data.values())[i], ha='center')

    plt.title(chart_title)
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.xticks(rotation=75)
    plt.legend(loc="upper right")

    fig_path = "charts/" + chart_title + '.png'
    plt.savefig(fig_path)

    return fig_path


def grapher_bar_trend(graph_list, x_name, y_name, chart_title, x_time=False):
    # graph list
    # COLUMN 1 - X values
    # COLUMN 2 - Values for y plot
    # COLUMN 3 - iteration
    # COLUMN 4 - category

    if graph_list is None:
        return

    cat_exists = (len(graph_list[0]) == 4)

    colors = ['b', 'g', 'r', 'c', 'm', 'y']
    color_val = 0

    x_column = [row[0] for row in graph_list]
    y_column = [row[1] for row in graph_list]

    graph_dict = {}
    total_dates = 1

    if x_time:
        for i in range(24):
            if cat_exists:
                graph_dict[str(i)] = {}
                for c in set([row[3] for row in graph_list]):
                    graph_dict[str(i)][c] = 0.0
            else:
                graph_dict[str(i)] = 0

        total_dates = len(set([row[2] for row in graph_list]))
        t_column = []
        for t in x_column:
            t_column.append(convert_to_time(t).strftime("%-H"))
            x_column = t_column

    y_plots = {}
    if cat_exists:
        c_column = [row[3] for row in graph_list]
        for cat in set(c_column):
            y_plots[cat] = []
        for x in range(len(x_column)):
            graph_dict[x_column[x]][c_column[x]] = graph_dict[x_column[x]][c_column[x]] + (y_column[x] / total_dates)
        for x in graph_dict.keys():
            for cat in graph_dict[x]:
                y_plots[cat].append(graph_dict[x][cat])
    else:
        for x in range(len(x_column)):
            if x_column[x] in graph_dict.keys():
                graph_dict[x_column[x]] = graph_dict[x_column[x]] + (y_column[x] / total_dates)
            else:
                graph_dict[x_column[x]] = int(y_column[x] / total_dates)

    fig1 = plt.figure()
    fig1.set_figwidth(10)
    fig1.set_figheight(5)

    if cat_exists:
        for cat in y_plots.keys():
            logger.log("Plotting: " + str(y_plots[cat]), source="GRPH")
            plt.plot(list(graph_dict.keys()), list(y_plots[cat]), label=cat, color=colors[color_val])
            color_val = color_val + 1
            if color_val == len(colors):
                color_val = 0
    else:
        plt.plot(list(graph_dict.keys()), list(graph_dict.values()))
        for i in range(len(graph_dict.keys())):
            plt.text(i, list(graph_dict.values())[i], list(graph_dict.values())[i], ha='center')

    plt.title(chart_title)
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.legend(loc="upper right")

    fig_path = "charts/" + chart_title + '.png'
    plt.savefig(fig_path)

    return fig_path


def grapher_trend(graph_list, x_name, y_name, chart_title, size=False):
    colors = ['b', 'g', 'r', 'c', 'm', 'y']
    color_val = 0

    t_column = [row[0] for row in graph_list]

    fig1 = plt.figure()
    fig1.set_figwidth(10)
    fig1.set_figheight(5)

    if size:
        t_data = []
        y_data = [row[1] for row in graph_list]
        size_data = [row[2] for row in graph_list]

        for t in t_column:
            t_data.append(convert_to_time(t))

        plt.scatter(t_data, y_data,
                    c=size_data,
                    s=size_data,
                    alpha=0.5,
                    cmap="jet")

    else:
        data, total_data = extractor([row[0] for row in graph_list],
                                     [row[1] for row in graph_list],
                                     [row[2] for row in graph_list], convert_time=True)
        for cat in data.keys():
            plt.scatter(list(data[cat].keys()), list(data[cat].values()),
                        color=colors[color_val],
                        alpha=0.5,
                        label=cat)

            color_val = color_val + 1
            if color_val == len(colors):
                color_val = 0

    plt.title(chart_title)
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.legend(loc="upper right")

    fig_path = "charts/" + chart_title + '.png'
    plt.savefig(fig_path)

    return fig_path


def grapher_simple_trend(graph_list, x_name, y_name, chart_title):
    fig1 = plt.figure()
    fig1.set_figwidth(10)
    fig1.set_figheight(5)

    plt.plot([row[0] for row in graph_list], [row[1] for row in graph_list])

    plt.title(chart_title)
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.xticks(rotation=75)
    plt.legend(loc="upper right")

    fig_path = "charts/" + chart_title + '.png'
    plt.savefig(fig_path)

    return fig_path


def grapher_weight_trend(graph_list, chart_title):
    fig1 = image.imread('resources/baby_weight_6m.png')

    # 0 days = 196
    # 91 days = 738

    # 1.7kg = 903
    # 11.3kg = 214

    x = []
    y = []

    for row in graph_list:
        days = (convert_to_date(row[0]) - datetime.strptime("2023/12/23", "%Y/%m/%d")).days
        x.append(196 + (days * 542 / 91))
        y.append(((903 - 214) * row[1] / (1.7 - 11.3)) + 1025)

    plt.plot(x, y)
    plt.axis('off')
    plt.imshow(fig1)
    fig_path = "charts/" + chart_title + '.png'
    plt.savefig(fig_path)

    return fig_path
