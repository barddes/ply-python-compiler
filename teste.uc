int checkPrime_unoptmized(int n) {
    int i, isPrime = 1;
    for (i = 2; i <= n/2; ++i) {
        if (n % i == 0) {
            isPrime = 0;
            break;
        }
        else{
            int a=1, b=2, c=3, d=4;
            if(a < b){
                print(a);
            }

            if(a<b && b > c){
                print(a);
            }

            if(!(a==d)){
                print(a);
            }

        }
    }
    i = 0;
    return isPrime;
}