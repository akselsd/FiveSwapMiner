#include <boost/multiprecision/cpp_int.hpp>
#include <cmath>
#include <vector>
#include <iostream>
#include <iterator>


using uint256_t = boost::multiprecision::uint256_t;
namespace mp = boost::multiprecision;

constexpr int W = 256;
constexpr size_t L = 10000;
constexpr int SHIFT_LENGTH = int(W/2);
constexpr size_t Y_LENGTH = size_t(L/2);

class FiveMiner
{
public:
    int mine_block(uint8_t* initial_hash);
    
private:
    std::vector<uint256_t> X = std::vector<uint256_t>(L, 0);    

};

extern "C" {
    FiveMiner* FiveMiner_new() { return new FiveMiner(); }
    int mine_block(FiveMiner* miner, uint8_t* initial_hash) {return miner->mine_block(initial_hash);}
}


/* Takes a 32 byte array of the block hash and mines according to the FiveSwap spec */
int FiveMiner::mine_block(uint8_t* initial_hash){
    
    mp::import_bits(X[0], initial_hash, initial_hash + 32*sizeof(uint8_t), 0, false);

    for(auto it = ++X.begin(); it < X.end(); ++it){
        uint256_t tmp = 5 * (*(it - 1));
        *it = (tmp >> SHIFT_LENGTH) | (tmp << SHIFT_LENGTH);
    }

    int popcount = 0;
    for (std::size_t idx = 0; idx < Y_LENGTH; ++idx){

        uint256_t y = X[idx] + X[L - idx - 1];

        /* Dirty hack to get underlying bytes */ 
        std::size_t size = y.backend().size();
        mp::limb_type* p = y.backend().limbs();

        /* This assumes sizeof(limb_type) == sizeof(unsigned long long)
           which might not be the case on all machines
         */
        for (std::size_t l_idx = 0; l_idx < size; ++l_idx) {
            popcount += __builtin_popcountll(*p);
            ++p;
        }
    }

    return popcount;
}
