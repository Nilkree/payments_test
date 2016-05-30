drop table if exists payments;
create table payments (
  id integer primary key autoincrement,
  amount real not null,
  currency integer not null,
  date text not null,
  description text
);