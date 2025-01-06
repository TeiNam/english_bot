# modules/mysql_connector.py
import mysql.connector
from mysql.connector import Error
from configs.mysql_setting import MYSQL_CONFIG
from typing import List, Dict, Any, Optional, Union, Tuple


class MySQLConnector:
    def __init__(self):
        self._connection = None  # 프라이빗 변수로 변경
        self.config = MYSQL_CONFIG
        self.is_transaction_active = False  # 트랜잭션 상태 추적

    def connect(self):
        """데이터베이스 연결"""
        try:
            if not self._connection or not self._connection.is_connected():
                self._connection = mysql.connector.connect(**self.config)
                print("MySQL 데이터베이스 연결 성공")
        except Error as e:
            print(f"MySQL 연결 오류: {e}")
            raise

    def get_connection(self):
        """현재 연결 반환"""
        self.connect()  # 연결이 없으면 새로 생성
        return self._connection

    def close(self):
        """데이터베이스 연결 종료"""
        try:
            if self._connection and self._connection.is_connected():
                if not self.is_transaction_active:  # 트랜잭션 중이 아닐 때만 닫기
                    self._connection.close()
                    self._connection = None
                    print("MySQL 연결이 종료되었습니다.")
        except Error as e:
            print(f"연결 종료 오류: {e}")

    def begin_transaction(self):
        """트랜잭션 시작"""
        self.connect()
        self._connection.start_transaction()
        self.is_transaction_active = True

    def commit_transaction(self):
        """트랜잭션 커밋"""
        if self._connection and self.is_transaction_active:
            self._connection.commit()
            self.is_transaction_active = False
            self.close()

    def rollback_transaction(self):
        """트랜잭션 롤백"""
        if self._connection and self.is_transaction_active:
            self._connection.rollback()
            self.is_transaction_active = False
            self.close()

    def escape_quotes(self, params: Union[dict, tuple, None]) -> Union[dict, tuple, None]:
        """파라미터의 문자열 값에서 큰따옴표 이스케이프 처리"""
        if params is None:
            return None

        if isinstance(params, dict):
            return {
                key: value.replace('"', '\\"') if isinstance(value, str) else value
                for key, value in params.items()
            }
        elif isinstance(params, tuple):
            return tuple(
                value.replace('"', '\\"') if isinstance(value, str) else value
                for value in params
            )
        return params

    def execute_query(self, query: str, params: Union[tuple, dict, None] = None, fetch: bool = True) -> Optional[
        List[Dict]]:
        """SQL 쿼리 실행을 위한 공통 메서드"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)

            # 파라미터의 큰따옴표 이스케이프 처리
            escaped_params = self.escape_quotes(params)

            cursor.execute(query, escaped_params)

            if fetch:
                result = cursor.fetchall()
                return result
            else:
                connection.commit()
                return {"affected_rows": cursor.rowcount}

        except Error as e:
            print(f"쿼리 실행 오류: {e}")
            if not fetch:
                connection.rollback()
            raise
        finally:
            cursor.close()

    def select(self,
               table: str,
               columns: List[str] = None,
               where: Dict = None,
               order_by: str = None,
               limit: int = None) -> List[Dict]:
        """
        SELECT 쿼리 실행

        Args:
            table (str): 테이블 이름
            columns (List[str]): 조회할 컬럼 리스트
            where (Dict): WHERE 조건
            order_by (str): ORDER BY 조건
            limit (int): LIMIT 값

        Returns:
            List[Dict]: 조회 결과
        """
        columns_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {columns_str} FROM {table}"
        params = {}

        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %({key})s")
                params[key] = value
            query += " WHERE " + " AND ".join(conditions)

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, params)

    # utils/mysql_connector.py의 insert 메서드 부분

    def insert(self, table: str, data: Union[Dict, List[Dict]]) -> Dict:
        """
        INSERT 쿼리 실행

        Args:
            table (str): 테이블 이름
            data (Union[Dict, List[Dict]]): 삽입할 데이터

        Returns:
            Dict: 영향받은 행 수와 마지막 삽입된 ID
        """
        if not data:
            raise ValueError("데이터가 비어있습니다.")

        # 단일 딕셔너리를 리스트로 변환
        if isinstance(data, dict):
            data = [data]

        columns = list(data[0].keys())
        placeholders = ', '.join([f'%({col})s' for col in columns])
        columns_str = ', '.join(columns)

        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(query, data[0])  # 현재는 단일 레코드만 처리
            connection.commit()

            last_id = cursor.lastrowid
            affected_rows = cursor.rowcount

            return {
                'id': last_id,
                'affected_rows': affected_rows
            }

        except Error as e:
            print(f"INSERT 쿼리 실행 오류: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()

    def update(self, table: str, data: Dict, where: Dict) -> Dict:
        """
        UPDATE 쿼리 실행

        Args:
            table (str): 테이블 이름
            data (Dict): 업데이트할 데이터
            where (Dict): WHERE 조건

        Returns:
            Dict: 영향받은 행 수
        """
        if not data or not where:
            raise ValueError("데이터와 조건이 모두 필요합니다.")

        try:
            # SET 절 생성 (using named parameters)
            set_clauses = []
            params = {}

            for key, value in data.items():
                set_clauses.append(f"{key} = %({key})s")
                params[key] = value

            # WHERE 절 생성
            where_clauses = []
            for key, value in where.items():
                where_key = f"where_{key}"  # 파라미터 이름 충돌 방지
                where_clauses.append(f"{key} = %({where_key})s")
                params[where_key] = value

            set_clause = ", ".join(set_clauses)
            where_clause = " AND ".join(where_clauses)

            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(query, params)
            connection.commit()

            return {
                'affected_rows': cursor.rowcount
            }

        except Error as e:
            print(f"UPDATE 쿼리 실행 오류: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()

    def delete(self, table: str, where: Dict) -> Dict:
        """
        DELETE 쿼리 실행

        Args:
            table (str): 테이블 이름
            where (Dict): WHERE 조건

        Returns:
            Dict: 영향받은 행 수
        """
        if not where:
            raise ValueError("삭제 조건이 필요합니다.")

        where_clause = " AND ".join([f"{key} = %({key})s" for key in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"

        return self.execute_query(query, where, fetch=False)

    def execute_raw_query(self, query: str, params: Union[tuple, dict, list, None] = None) -> Optional[List[Dict]]:
        """직접 작성한 SQL 쿼리 실행"""
        connection = None
        cursor = None
        try:
            # 새로운 연결 생성
            connection = mysql.connector.connect(**self.config)
            cursor = connection.cursor(dictionary=True, buffered=True)  # buffered=True 추가

            if isinstance(params, (list, tuple)):
                cursor.execute(query, params)
            elif isinstance(params, dict):
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESC')):
                result = cursor.fetchall()
                return result
            else:
                connection.commit()
                return {"affected_rows": cursor.rowcount}

        except Error as e:
            print(f"쿼리 실행 오류: {e}")
            if connection and not query.strip().upper().startswith(('SELECT', 'SHOW', 'DESC')):
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()