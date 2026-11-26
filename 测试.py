import time

start = time.perf_counter()
class Solution(object):
    def divide_version_1(self, dividend, divisor):
        #时间复杂度：O(n)
        rem = 0
        r = 0
        if abs(dividend) != abs(divisor):
            if dividend > 0 and divisor > 0:
                while dividend >= divisor:
                    dividend -= divisor
                    rem += 1
            elif dividend < 0 < divisor:
                d = abs(dividend)
                while d >= divisor:
                    d -= divisor
                    r += 1
                rem  = -r
            elif dividend < 0 and divisor < 0:
                d1 = abs(dividend)
                d2 = abs(divisor)
                while d1 >= d2:
                    d1 -= d2
                    r += 1
                rem = r
            elif dividend > 0 >divisor:
                d2 = abs(divisor)
                while dividend >= d2:
                    dividend -= d2
                    r += 1
                rem = -r
        elif dividend == divisor:
            rem = 1
        elif dividend == -divisor:
            rem = -1
        return rem
    def divide_version_2(self, dividend, divisor):
        #时间复杂度：O(log^2 n)
        if - 2 ** 31 < dividend < 2 ** 31:
            rem = 0
            q = 0
            d1 = abs(dividend)
            d2 = abs(divisor)
            if abs(dividend) != abs(divisor):
                if dividend > 0 and divisor > 0:
                    while dividend >= divisor:
                        r = 0
                        while dividend >= (divisor << (r + 1)):
                            r += 1
                        q += 1 << r#累计商
                        dividend -= divisor << r
                        rem = q

                elif dividend < 0 < divisor:
                   #d1 = abs(dividend)
                   while d1 >= divisor:
                    r = 0
                    while d1 >= (divisor << (r + 1)):
                        r += 1
                    q += 1 << r  # 累计商
                    d1 -= divisor << r
                    rem = -q

                elif dividend < 0 and divisor < 0:
                    while d1 >= d2:
                      r = 0
                      while d1 >= (d2 << (r + 1)):
                          r += 1
                      q += 1 << r  # 累计商
                      d1 -= d2 << r
                      rem = q

                elif dividend > 0 >divisor:

                    #d2 = abs(divisor)
                  while dividend >= d2:
                      r = 0
                      while dividend >= (d2 << (r + 1)):
                          r += 1
                      q += 1 << r#累计商
                      dividend -= d2 << r
                      rem = -q

            elif dividend == divisor:
                rem = 1
            elif dividend == -divisor:
                rem = -1
            return rem
        elif dividend <= - (2 ** 31):
            rem = - 2 ** 31 + 1
        elif dividend >=  (2 ** 31):
            rem =  2 ** 31 - 1
        return rem





if __name__ == '__main__':
    sol = Solution()
    dividend, divisor = -2 ** 31, -1
    #result = sol.divide_version_1(dividend, divisor)
    result = sol.divide_version_2(dividend, divisor)
    print(result)
    end = time.perf_counter()  # 结束计时
    print(f"运行时间: {end - start:.6f} 秒")
