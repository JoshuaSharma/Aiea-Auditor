% Facts
conducts(metal, electricity).
not(conducts(insulator, electricity)).

% Rules
metal(X) :- made_of(X, iron).
conducts(X, electricity) :- metal(X).

% Specific facts
made_of(nails, iron).

% Query
query(nails_conducts_electricity) :- conducts(nails, electricity).