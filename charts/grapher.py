from datetime import datetime, timedelta

from matplotlib import pyplot as plt


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
        i = i+1

    return data, total_data


def grapher_category(graph_list, x_name, y_name, chart_title):
    colors = ['b', 'g', 'r', 'c', 'm', 'y']
    color_val = 0

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
    plt.legend(loc="upper right")

    fig_path = "charts/" + chart_title + '.png'
    plt.savefig(fig_path)

    return fig_path
