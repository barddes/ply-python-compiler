int main() {
    int x =2, y, z;
    y = ++x;
    z = x++;
    assert y == 3 && z == 3;
    if(x==x){
        print(x);
        for(int k = 0; k < 10; k++)
            print(k);
    }
    else{
        print(y);
    }
    return 0;
}
