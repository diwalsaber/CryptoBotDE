CREATE TABLE Symbol (
SymbolId integer,
Name varchar,
Description varchar,
PRIMARY KEY (SymbolId));

CREATE TABLE CandleStickHistorical (
OpenTime timestamp,
SymbolId integer,
Interval varchar(5),
OpenPrice float,
ClosePrice float,
BaseVolume float,
NumberTrades int,
TakerBuyBase float,
TakerBuyQuote float,
PRIMARY KEY (OpenTime, SymbolId, Interval),
FOREIGN KEY (SymbolId) REFERENCES Symbol(symbolid));


drop table CandleStickHistorical;
CREATE TABLE CandleStickHistorical (
    OpenTime timestamp, 
    SymbolId integer NOT NULL,
    OpenPrice FLOAT,
    HighPrice FLOAT,
    LowPrice FLOAT,
    ClosePrice FLOAT,
    BaseVolume FLOAT,
    CloseTime timestamp,
    QuoteVolume FLOAT,
    NumberTrades FLOAT,
    TakerBuyBase FLOAT,
    TakerBuyQuote FLOAT,
    PRIMARY KEY (OpenTime, SymbolId),
    FOREIGN KEY (SymbolId) REFERENCES Symbol(SymbolId)
);

delete from  CandleStickHistorical;

commit;

SELECT create_hypertable('CandleStickHistorical', 'opentime');


SELECT create_hypertable('CandleStickRealTime', 'opentime');

create sequence seq_symbol;

select * from symbol;
commit;

select count(*) from CandleStickHistorical ;


delete from CandleStickHistorical ;

INSERT INTO Symbol (SymbolId, Name, Description) VALUES (nextval('seq_symbol'), 'BTCUSDT', 'None');


select count(*) from tmp;

select max(opentime) from CandleStickHistorical where opentime < current_date 

select min(opentime) from CandleStickHistorical where opentime > current_date;

SELECT time_bucket('1 hours', opentime) AS bucket, COUNT(*) AS nb_datas
FROM CandleStickHistorical
GROUP BY bucket
HAVING COUNT(*) < 5
ORDER BY bucket desc limit 100;


SELECT time_bucket('5 minutes', opentime) AS bucket, COUNT(*) AS nb_datas
FROM CandleStickHistorical
GROUP BY bucket

SELECT empty_periods('5 minutes', opentime) AS period
FROM CandleStickHistorical
ORDER BY period DESC;


insert into CandleStickHistorical (opentime, symbolid) values (current_timestamp, 5);
commit;

select max(opentime) from CandleStickHistorical;