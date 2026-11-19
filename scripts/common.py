"""Spark-частина: читання сирих даних і чистка (етап 0). Правила беруться з rules.py."""
from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

import rules

SCHEMA = StructType([StructField(c, StringType()) for c in rules.COLS])


def session(app: str) -> SparkSession:
    spark = SparkSession.builder.appName(app).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def read_raw(spark: SparkSession, path: str, fmt: str = "csv") -> DataFrame:
    if fmt == "parquet":
        return spark.read.parquet(path)
    # escape='"': у CSV лапки всередині поля подвоюються ("") за RFC 4180
    return spark.read.csv(path, schema=SCHEMA, header=True, escape='"')


def _nonempty(c: Column) -> Column:
    return c.isNotNull() & (c != "")


def fixed_product() -> Column:
    """F1 + F3: trim і зведення старих назв продуктів до чинних."""
    p = F.trim("product")
    mapping = F.create_map(*[F.lit(x) for kv in rules.PRODUCT_MAP.items() for x in kv])
    cards = F.when(F.col("sub_product").isin(*rules.CREDIT_CARD_SUBS), "Credit card").otherwise("Prepaid card")
    return F.when(p == rules.MERGED_CARDS, cards).otherwise(F.coalesce(mapping[p], p))


def keep_condition() -> Column:
    """Рядок лишається, якщо не спрацювало жодне з правил D1-D3."""
    d1 = F.col("company_response").isin(*rules.CLOSED)
    d2 = _nonempty(F.trim("company")) & _nonempty(F.trim("product")) & _nonempty(F.trim("issue"))
    d3 = F.coalesce(F.col("date_received").rlike(rules.DATE_REGEX), F.lit(False))
    return d1 & d2 & d3


def clean(raw: DataFrame) -> DataFrame:
    """Етап 0: відкидає D1-D3, виправляє F1-F3, лишає 5 колонок."""
    return raw.where(keep_condition()).select(
        F.upper(F.trim("company")).alias("company"),           # F1 + F2
        fixed_product().alias("product"),                      # F1 + F3
        F.trim("issue").alias("issue"),                        # F1
        F.substring("date_received", 1, 7).alias("month"),
        F.col("company_response").isin(*rules.RELIEF).cast("int").alias("relief"),
    )
