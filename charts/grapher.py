from datetime import datetime, timedelta

from matplotlib import pyplot as plt


def extractor(graph_dict, x_column, cat_column, data_column, convert_time=False):
    data = {}
    total_data = {}

    for val in graph_dict.keys():
        if convert_time:
            format_string = "%H:%M:%S"
            x = datetime.strptime(graph_dict[val][x_column], format_string)
            x = x.replace(second=0, microsecond=0, minute=0, hour=x.hour)+timedelta(hours=x.minute//30)
        else:
            x = graph_dict[val][x_column]

        category = graph_dict[val][cat_column]

        if category not in data.keys():
            data[category] = {}

        if x in data[category].keys():
            data[category][x] = data[category][x] + float(graph_dict[val][data_column])
        else:
            data[category][x] = float(graph_dict[val][data_column])

        if x in total_data.keys():
            total_data[x] = total_data[x] + float(graph_dict[val][data_column])
        else:
            total_data[x] = float(graph_dict[val][data_column])

    return data, total_data


def grapher_category_dictionary(graph_dict, x_column, cat_column, data_column, x_name, y_name, chart_title):
    colors = ['b', 'g', 'r', 'c', 'm', 'y']
    color_val = 0

    data, total_data = extractor(graph_dict, x_column, cat_column, data_column)

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


def grapher_trend(graph_dict, t_column, cat_column, data_column, x_name, y_name, chart_title, size=False):
    colors = ['b', 'g', 'r', 'c', 'm', 'y']
    color_val = 0

    fig1 = plt.figure()
    fig1.set_figwidth(10)
    fig1.set_figheight(5)

    if size:
        t_data = []
        y_data = []
        size_data = []

        for key in graph_dict.keys():
            t_data.append(graph_dict[key][t_column])
            y_data.append(graph_dict[key][cat_column])
            size_data.append(float(graph_dict[key][data_column]))

        plt.scatter(t_data, y_data,
                    c=size_data,
                    s=size_data,
                    alpha=0.5,
                    cmap="jet")

    else:
        data, total_data = extractor(graph_dict, t_column, cat_column, data_column, convert_time=True)
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
