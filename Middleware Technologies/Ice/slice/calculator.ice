
#ifndef CALC_ICE
#define CALC_ICE

module Demo
{
  sequence<long> longList; // Zadanie 14.
  enum operation { MIN, MAX, AVG };
  
  exception NoInput
  {
    string reason; // Zadanie 14.
  };

  struct A
  {
    short a;
    long b;
    float c;
    string d;
  }

  interface Calc
  {
    idempotent long add(int a, int b); // Zadanie 15.
    idempotent long subtract(int a, int b); // Zadanie 15.
    void op(A a1, short b1); //załóżmy, że to też jest operacja arytmetyczna ;)
    idempotent long avg(longList a) throws NoInput; // Zadanie 14., 15.
  };

};

#endif
