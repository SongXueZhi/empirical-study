import pandas as pd
import matplotlib.pyplot as plt

black_list = ['No', 'NO']

# Categories
action_type = 'Bic Action Type'
self_error = 'Intrinsic Errors'
suitable_error = 'Compatibility Errors'
knowledge = 'Knowledge'
feature_interaction = 'Feature Interaction'
fix_location = 'Location With Fixing Changes'


def preprocess_data(_data: pd.DataFrame):
    for index, row in _data.iterrows():
        c_bic_ac = row[action_type].split(',')
        # process the case that there are multiple action types, and clean action types
        if len(c_bic_ac) > 1:
            for ac in c_bic_ac:
                if ac == 'enhance' or ac == 'enhancement ':
                    _data.loc[index, action_type] = 'feat'
                if ac == 'Reimpl.':
                    _data.loc[index, action_type] = 'refactor'
        else:
            if c_bic_ac[0] == 'enhance' or c_bic_ac[0] == 'enhancement ':
                _data.loc[index, action_type] = 'feat'
            if c_bic_ac[0] == 'Reimpl.':
                _data.loc[index, action_type] = 'refactor'

        # process the case that both self_error and suitable_error exist
        if row[self_error] != 'No' and row[suitable_error] != 'No':
            _data.loc[index, self_error] = 'No'

        # normalize the value of knowledge
        knowledge_cell = row[knowledge]

        if not isinstance(knowledge_cell, str):  # there may exists some nones
            _data.loc[index, knowledge] = 'Programming'
        elif '项目知识' in knowledge_cell and '领域知识' not in knowledge_cell:
            _data.loc[index, knowledge] = 'Project'
        elif '项目知识' not in knowledge_cell and '领域知识' in knowledge_cell:
            _data.loc[index, knowledge] = 'Domain'
        elif '项目知识' in knowledge_cell and '领域知识' in knowledge_cell:
            _data.loc[index, knowledge] = 'Project & Domain'
        else:
            _data.loc[index, knowledge] = 'Programming'
    # print(_data[action_type].unique())
    return _data


model_cnt = 7
total_bugs = 280
data = pd.read_csv('id-model.csv')
data = preprocess_data(data)
columns = list(data.columns)
# print(columns)
models = columns[1:model_cnt + 1]


def expand_rows_if_multi_tags(_df: pd.DataFrame, _tag_column: str):
    # if there are multiple tags in the tag column, split them and expand the rows
    df_expanded = _df.assign(**{_tag_column: _df[_tag_column].str.split(',')}).explode(_tag_column)
    return df_expanded.dropna()


def count_0_1_by_column(_tag_column: str, _expand=False):  # now _expand is true may cause error
    df = pd.DataFrame(data, columns=columns)
    # print(df[_tag_column].unique())
    if _expand:
        df = expand_rows_if_multi_tags(df, _tag_column)  # split the value of tag column if there are multiple types

    _result = {}
    for model in models:
        _result[model] = {}
        for tag in df[_tag_column].unique():
            filtered_df = df[df[_tag_column] == tag]
            counts = filtered_df[model].value_counts().to_dict()
            _result[model][tag] = {
                0: counts.get(0, 0),
                1: counts.get(1, 0)
            }
    return _result


def draw_picture(_tag_column: str):
    # 进行统计
    _result = count_0_1_by_column(_tag_column)

    width = 0.85
    x = range(model_cnt)

    # 创建图形和坐标轴
    fig, ax = plt.subplots(figsize=(12, 8))
    bottom = [0] * model_cnt

    for tag in _result[models[0]].keys():
        heights = []
        if tag in black_list:
            heights = [0] * model_cnt
            ax.bar(x, heights, width, bottom=bottom, label='')
        else:
            for model in models:
                heights.append(_result[model][tag][1])
            ax.bar(x, heights, width, bottom=bottom, label=tag)

        for i, height in enumerate(heights):
            bottom[i] += height

    ax.set_xlabel('Models')
    ax.set_ylabel('Counts')
    ax.set_title(f'Counts by {_tag_column}')
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45)
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.show()
    fig.savefig(f'{_tag_column}.png')


def draw_tables(_results_dict: dict):
    table_columns = ['Feature', 'Total Count'] + models
    table_per_columns = ['Feature'] + models

    # print(results_dict['self_error_result'])

    dataframe = pd.DataFrame(columns=table_columns)
    dataframe_per = pd.DataFrame(columns=table_per_columns)

    for key, value in _results_dict.items():
        for tag in value[models[0]].keys():
            if tag in black_list:
                continue
            row = [tag, f'{value[models[0]][tag][0] + value[models[0]][tag][1]}']
            row_per = [tag]
            for model in models:
                val = value[model][tag][1]
                if val == 0:
                    row.append('--')
                    row_per.append('0.00%')
                else:
                    row.append(f'{val}')
                    row_per.append(f'{val / (val + value[model][tag][0]) * 100:.2f}%')
            dataframe.loc[len(dataframe)] = row
            dataframe_per.loc[len(dataframe_per)] = row_per
    row = ['Total', f'{total_bugs}']
    row_per = ['Total']

    for model in models:
        pred_sum = 0
        for tag in _results_dict['self_error_result'][models[0]].keys():
            pred_sum += _results_dict['self_error_result'][model][tag][1]
        row.append(f'{pred_sum}')
        row_per.append(f'{pred_sum / total_bugs * 100:.2f}%')

    dataframe.loc[len(dataframe)] = row
    dataframe_per.loc[len(dataframe_per)] = row_per

    dataframe.to_csv('table.csv', index=False)
    dataframe_per.to_csv('table_per.csv', index=False)


results_dict = {'self_error_result': count_0_1_by_column(self_error),
                'suitable_error_result': count_0_1_by_column(suitable_error),
                'feature_interaction_result': count_0_1_by_column(feature_interaction),
                'location_result': count_0_1_by_column(fix_location),
                'knowledge_result': count_0_1_by_column(knowledge)}
draw_tables(_results_dict=results_dict)

# draw_picture(_tag_column=self_error)
# draw_picture(_tag_column=suitable_error)
# draw_picture(_tag_column=feature_interaction)
# draw_picture(_tag_column=fix_location)
# draw_picture(_tag_column=knowledge)
