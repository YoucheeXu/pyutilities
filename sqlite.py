#!/usr/bin/python3
# -*- coding: utf-8 -*-
# import os
import sqlite3
from typing import Any


class SQLite:
    def __init__(self):
        self.__conn: sqlite3.Connection
        self.__cur: sqlite3.Cursor

    # def Open(self, path: str) -> str:
        # _this = this;
        # return Promise((resolve, reject) => {
            # _this.db = sqlite3.Database(path,
                # (err: Error | null) => {
                    # if (err) {
                        # console.error("Open error: " + err.message);
                        # reject("Open error: " + err.message);
                    # }
                    # else {
                        # print(path + " opened");
                        # resolve(path + " opened");
                    # }
                # }
            # )
        # })
    # }
    def open(self, file_: str) -> tuple[int, str]:
        # if not os.path.isfile(file_):
            # return -1, f"{file_} doesn't exit!"

        self.__conn = sqlite3.connect(file_)
        if self.__conn:
            self.__cur = self.__conn.cursor()
        else:
            return -1, f"fail to open {file_}"

        return 1, file_ + "is OK to open!"

    # any query: insert/delete/update
    def execute1(self, sql: str, parameters = ()) -> bool:
        ret = self.__cur.execute(sql, parameters)
        if not ret:
            return False

        self.__conn.commit()
        return True

    def execute(self, sql: str, parameters = ()):
        _ = self.__cur.execute(sql, parameters)

    def commit(self):
        self.__conn.commit()

    def get(self, query: str) -> Any:
        # first row read
        _ = self.__cur.execute(query)
        records = self.__cur.fetchone()
        return records[0]

    def each(self, query: str) -> Any:
        # set of rows read
        # for row in :
            # yield row
        yield from self.__cur.execute(query)

    def close(self) -> bool:
        if self.__cur:
            self.__cur.close()
        if self.__conn:
            self.__conn.close()
        return True
