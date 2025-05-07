% Facts
conducts_electricity(metal).
not(conducts_electricity(insulator)).
is_metal(iron).
made_of(nails, iron).

% Rule
conducts_electricity(X) :- made_of(X, Material), is_metal(Material), conducts_electricity(metal).

% Query if nails conduct electricity
query :- conducts_electricity(nails).