from regs4j.sql_manager import MySQLDatabase
import pandas as pd

def main():
    db = MySQLDatabase("10.176.34.95", "root", "1235", "code_annotation2")
    db.connect()
    result = db.fetch_query("select project_name, bic from regressions_all where project_name = 'alibaba_fastjson'")
    db.connect()
    # 将结果转换为 pandas DataFrame
    df = pd.DataFrame(result, columns=['project_name', 'bic'])

    # 对 'project_name' 列中的下划线进行分割并只保留后半部分
    df['project_name'] = df['project_name'].str.split('_').str[-1]

   # 将 'bic' 列重命名为 'commit_hash'
    df.rename(columns={'bic': 'commit_hash'}, inplace=True)

    # 对 'commit_hash' 列去重
    df_unique_commit_hash = df.drop_duplicates(subset=['commit_hash'])

    # 保存结果为 PKL 文件
    df_unique_commit_hash.to_pickle('./data/alibaba_fastjson_unique_bic.pkl')

    print("数据已成功保存为PKL文件：./data/bug_unique_bic.pkl")

if __name__ == "__main__":
    main()

    