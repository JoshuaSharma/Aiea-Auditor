% Facts
conducts_electricity(metal).
does_not_conduct_electricity(insulator).
made_of(iron, metal).
made_of(nail, iron).

% Rules
conducts_electricity(Object) :- made_of(Object, Material), conducts_electricity(Material).

% Query
% To check if nails cannot conduct electricity, we negate the conducts_electricity predicate.
% Answer the query: does_not_conduct_electricity(nail) or conduct_electricity(nail).

% The statement "Nails cannot conduct electricity." is false because nails are made of iron,
% and iron is a metal, and metals conduct electricity.