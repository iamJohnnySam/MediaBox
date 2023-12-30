from matplotlib import pyplot as plt


def grapher_category_dictionary(graph_dict, x_column, cat_column, data_column, x_name, y_name, chart_title):
    colors = ['b', 'g', 'r', 'c', 'm', 'y']
    color_val = 0

    bar_width = 0.25

    data = {}
    total_data = {}

    for val in graph_dict.keys():
        title = graph_dict[val][x_column]
        category = graph_dict[val][cat_column]

        if category not in data.keys():
            data[category] = {}

        if title in data[category].keys():
            data[category][title] = data[category][title] + float(graph_dict[val][data_column])
        else:
            data[category][title] = float(graph_dict[val][data_column])

        if title in total_data.keys():
            total_data[title] = total_data[title] + float(graph_dict[val][data_column])
        else:
            total_data[title] = float(graph_dict[val][data_column])

    fig1 = plt.figure()
    fig1.set_figwidth(10)
    fig1.set_figheight(5)

    prev_bar = None

    for cat in data.keys():
        plt.bar(list(data[cat].keys()), list(data[cat].values()), color=colors[color_val], label=cat, bottom=prev_bar)
        prev_bar = cat

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
