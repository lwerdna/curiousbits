#!/usr/bin/env python

def factorial(n):
	if n==0: return 1;
	if n<0: return -factorial(-n);
	return n * factorial(n-1)

def P(n, k):
	return factorial(n) // factorial(k)

def C(n, k):
	return P(n, k) // factorial(n-k)

def MultiChoose(n, k):
	return C(n + (k-1), k)

def StarsBars1(n, k):
	return C(n-1, k-1)

def StarsBars2(n, k):
	return MultiChoose(n+1, k-1)
