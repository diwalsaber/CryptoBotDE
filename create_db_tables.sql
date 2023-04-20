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

CREATE TABLE CandleStickRealTime (
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

SELECT create_hypertable('CandleStickHistorical', 'opentime');


SELECT create_hypertable('CandleStickRealTime', 'opentime');