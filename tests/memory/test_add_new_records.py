from walnut.memory.preprocess_records import load_file, preprocess_chat_data, write_daily_record_to_file
from datetime import date, timedelta
from walnut.memory.loader import load_ac_records_documents
from walnut.memory.db import DB

def test_add_new_records():
    # file_path = './docs/DNbase.xlsx'
    # df = load_file(file_path)
    # daily_texts = preprocess_chat_data(df)

    # start_date = date(2024, 9, 14)
    # end_date = date(2024, 10, 10)
    output_dir='./outputs/daily_records'
    # current_date = start_date
    # while current_date <= end_date:
    #     write_daily_record_to_file(daily_texts, current_date, output_dir='./outputs/daily_records')
    #     current_date += timedelta(days=1)
    documents = load_ac_records_documents(path=output_dir)
    print(documents)
    dir_path = './testDB'
    db = DB(sqlitedb_path=f"{dir_path}/sqlite.db", vecdb_path=f"{dir_path}/chroma")
    db.insert_documents(documents)


