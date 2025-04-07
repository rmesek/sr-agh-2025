
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
    long add(int a, int b);
    long subtract(int a, int b);
    void op(A a1, short b1); //załóżmy, że to też jest operacja arytmetyczna ;)
    long avg(longList a) throws NoInput; // Zadanie 14.
  };

};

#endif
