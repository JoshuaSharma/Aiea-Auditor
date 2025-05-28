% === Facts ===
animal(tweety).
animal(opus).
animal(whiskers).
animal(simba).
animal(dumbo).
animal(sharky).
animal(eagle1).
animal(falcon1).
animal(nemo).
animal(baloo).
animal(bambi).
animal(garfield).
animal(froggy).
animal(slinky).
animal(scooby).
animal(pluto).
animal(tiger1).
animal(penguin1).

bird(tweety).
bird(opus).
bird(eagle1).
bird(falcon1).
bird(penguin1).

mammal(whiskers).
mammal(simba).
mammal(baloo).
mammal(bambi).
mammal(garfield).
mammal(scooby).
mammal(pluto).
mammal(tiger1).

fish(nemo).
fish(sharky).

reptile(slinky).
amphibian(froggy).
elephant(dumbo).

% === Rules ===

% Rule 1: All birds are animals
is_animal(X) :- bird(X).
is_animal(X) :- mammal(X).
is_animal(X) :- fish(X).
is_animal(X) :- reptile(X).
is_animal(X) :- amphibian(X).
is_animal(X) :- elephant(X).

% Rule 2: Penguins are birds that cannot fly
penguin(X) :- bird(X), \+ can_fly(X).

% Rule 3: Birds can usually fly unless specified
can_fly(X) :- bird(X), \+ no_fly(X).

% Rule 4: Known birds that cannot fly
no_fly(opus).
no_fly(penguin1).

% Rule 5: Mammals can walk
can_walk(X) :- mammal(X).

% Rule 6: Fish can swim
can_swim(X) :- fish(X).

% Rule 7: All elephants are mammals
mammal(X) :- elephant(X).
