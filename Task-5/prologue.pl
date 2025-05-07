:- dynamic conducts_electricity/1.
:- dynamic metal/1.
:- dynamic insulator/1.
:- dynamic made_of/2.

% Facts
metal(metals).
insulator(insulators).
conducts_electricity(metals).
conducts_electricity(X) :- metal(X).
made_of(nails, iron).
metal(iron).

% Query: Are nails conductive?
conducts_electricity(nails) :- made_of(nails, X), metal(X).