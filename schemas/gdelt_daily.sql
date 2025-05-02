CREATE TABLE gdelt_daily (
  SQLDATE               VARCHAR,
  MonthYear             INTEGER,
  Year                  INTEGER,
  FractionDate          DOUBLE,
  Actor1Code            VARCHAR,
  Actor1Name            VARCHAR,
  Actor2Code            VARCHAR,
  Actor2Name            VARCHAR,
  IsRootEvent           BOOLEAN,
  EventCode             VARCHAR,
  GoldsteinScale        DOUBLE,
  AvgTone               DOUBLE,
  ActionGeo_CountryCode VARCHAR,
  ActionGeo_Lat         DOUBLE,
  ActionGeo_Long        DOUBLE,
  SOURCE_FILE           VARCHAR
);
