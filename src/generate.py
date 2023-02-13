import psycopg2
from faker import Faker
import time
import random
from multiprocessing import Pool
import argparse


class FakeData:
    DefaultDataTypes = {"boolean": "pybool", "int": "pyint", "float8": "pyfloat", "text": "paragraph", "varchar": "pystr_format", "numeric": "pydecimal"}

    def __init__(self, conn) -> None:
        self._conn = conn
        self._cursor = conn.cursor()
        self._fake = Faker()
        self._current_table = {}
        Faker.seed(time.time())

    def generate_table_name(self) -> str:
        return "fake_table_" + self._fake.ean(length=13) + str(round(time.time() * 1e7))

    # datatypes: [(type_name, type_fake_func, fake_func_parameter)]
    def generate_column_list(self, datatypes: list, pk:bool = True):
        columns = []

        if pk:
            columns.append("id serial primary key".split(" "))

        column_names = []
        for t in datatypes:
            column_name = "fake_col_" + self._fake.sha1()

            while column_name in column_names:
                column_name = "fake_col_" + self._fake.sha1()

            column_names.append(column_name)
            columns.append(["fake_col_" + self._fake.sha1(), t])
        return columns

    def create_random_table(self, datatypes = None, pk = True, storage_params = {}) -> str:
        table_name = self.generate_table_name()
        while table_name in self._current_table.keys():
            table_name = self.generate_table_name()

        if not datatypes:
            datatypes = []
            for _ in range(6):
                k = random.choice(list(FakeData.DefaultDataTypes.keys()))
                datatypes.append(k)
        column_list = self.generate_column_list(datatypes, pk = pk)

        storage_parameters = (
            f"WITH ({','.join([f'{key}={storage_params[key]}' for key in storage_params.keys()])})"
        )

        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name}
            ({','.join([' '.join(map(str, l)) for l in column_list])})
            {storage_parameters if storage_params else ''};
        """

        self._cursor.execute(query)

        self._current_table[table_name] = column_list

        return table_name

    def insert_random_data(self, table_name, num_row:int = 10, column_list:list = []) -> None:
        if not column_list:
            column_list = self._current_table[table_name]
        data = []
        primary_col = None
        for _ in range(num_row):
            d = []
            for l in column_list:
                if "primary" in l and "key" in l:
                    primary_col = l
                    continue
                t = FakeData.DefaultDataTypes[l[1]]
                type_func = getattr(self._fake, t)
                d.append(type_func())
            data.append('(' + ','.join(map(lambda x: f"'{str(x)}'", d)) + ')')
        if primary_col:
            column_list.remove(primary_col)

        data = ','.join(data)
        query = f"""
            INSERT INTO {table_name}({','.join(map(lambda x: x[0], column_list))}) VALUES
            {data};
        """

        self._cursor.execute(query)

    def get_current_tables(self) -> dict:
        return self._current_table

def test(args:tuple = (), forever=False, num_row:int = 8000000):
    test_id = args[0]
    ao = args[1]
    num_row = args[2]
    command_args = args[3]

    f = open("logs/%d.log" % test_id, "w+")

    conn = psycopg2.connect(user=command_args.username,
                            host="127.0.0.1",
                            database=command_args.dbname)
    conn.autocommit = True

    while True:
        f.write(f"[{time.time()}] start generate\n")

        fd = FakeData(conn)
        if ao:
            table_name = fd.create_random_table(pk= False, storage_params={"appendoptimized": True})
        else:
            table_name = fd.create_random_table()

        f.write(f"[{time.time()}] create table %s\n" % table_name)

        count = 0
        while count < num_row:
            fd.insert_random_data(table_name, 10)
            count = count + 10

        f.flush()

        if not forever:
            break

    f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provide username and db name')
    parser.add_argument('username', type=str,
                    help='user of db')
    parser.add_argument('dbname', type=str,
                    help='db name')
    args = parser.parse_args()
    with Pool(20) as p:
        p.map(test, [(i, random.choice([True, False]), 8000000, args) for i in range(10)])
