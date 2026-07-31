.PHONY: all clean test

all: matMultp

clean:
	$(RM) -r matMultp tests/results

test: matMultp tests/a.txt tests/b.txt | tests/results
	./matMultp tests/a tests/b tests/results/c

tests/results:
	mkdir --parent $@

matMultp: main.c
	gcc $^ -o $@
