from __future__ import annotations

from contextlib import closing
from typing import Any

from psycopg2.extras import Json, RealDictCursor

from database.postgres import get_connection


DATASPACE_TYPE_CODE = "dataspace"
DATASPACE_TYPE_LOGO = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAG4AAABiCAYAAACxmeaAAAAEDmlDQ1BrQ0dDb2xvclNwYWNlR2VuZXJpY1JHQgAAOI2NVV1oHFUUPpu5syskzoPUpqaSDv41lLRsUtGE2uj+ZbNt3CyTbLRBkMns3Z1pJjPj/KRpKT4UQRDBqOCT4P9bwSchaqvtiy2itFCiBIMo+ND6R6HSFwnruTOzu5O4a73L3PnmnO9+595z7t4LkLgsW5beJQIsGq4t5dPis8fmxMQ6dMF90A190C0rjpUqlSYBG+PCv9rt7yDG3tf2t/f/Z+uuUEcBiN2F2Kw4yiLiZQD+FcWyXYAEQfvICddi+AnEO2ycIOISw7UAVxieD/Cyz5mRMohfRSwoqoz+xNuIB+cj9loEB3Pw2448NaitKSLLRck2q5pOI9O9g/t/tkXda8Tbg0+PszB9FN8DuPaXKnKW4YcQn1Xk3HSIry5ps8UQ/2W5aQnxIwBdu7yFcgrxPsRjVXu8HOh0qao30cArp9SZZxDfg3h1wTzKxu5E/LUxX5wKdX5SnAzmDx4A4OIqLbB69yMesE1pKojLjVdoNsfyiPi45hZmAn3uLWdpOtfQOaVmikEs7ovj8hFWpz7EV6mel0L9Xy23FMYlPYZenAx0yDB1/PX6dledmQjikjkXCxqMJS9WtfFCyH9XtSekEF+2dH+P4tzITduTygGfv58a5VCTH5PtXD7EFZiNyUDBhHnsFTBgE0SQIA9pfFtgo6cKGuhooeilaKH41eDs38Ip+f4At1Rq/sjr6NEwQqb/I/DQqsLvaFUjvAx+eWirddAJZnAj1DFJL0mSg/gcIpPkMBkhoyCSJ8lTZIxk0TpKDjXHliJzZPO50dR5ASNSnzeLvIvod0HG/mdkmOC0z8VKnzcQ2M/Yz2vKldduXjp9bleLu0ZWn7vWc+l0JGcaai10yNrUnXLP/8Jf59ewX+c3Wgz+B34Df+vbVrc16zTMVgp9um9bxEfzPU5kPqUtVWxhs6OiWTVW+gIfywB9uXi7CGcGW/zk98k/kmvJ95IfJn/j3uQ+4c5zn3Kfcd+AyF3gLnJfcl9xH3OfR2rUee80a+6vo7EK5mmXUdyfQlrYLTwoZIU9wsPCZEtP6BWGhAlhL3p2N6sTjRdduwbHsG9kq32sgBepc+xurLPW4T9URpYGJ3ym4+8zA05u44QjST8ZIoVtu3qE7fWmdn5LPdqvgcZz8Ww8BWJ8X3w0PhQ/wnCDGd+LvlHs8dRy6bLLDuKMaZ20tZrqisPJ5ONiCq8yKhYM5cCgKOu66Lsc0aYOtZdo5QCwezI4wm9J/v0X23mlZXOfBjj8Jzv3WrY5D+CsA9D7aMs2gGfjve8ArD6mePZSeCfEYt8CONWDw8FXTxrPqx/r9Vt4biXeANh8vV7/+/16ffMD1N8AuKD/A/8leAvFY9bLAAAAbGVYSWZNTQAqAAAACAAEARoABQAAAAEAAAA+ARsABQAAAAEAAABGASgAAwAAAAEAAgAAh2kABAAAAAEAAABOAAAAAAAAAJAAAAABAAAAkAAAAAEAAqACAAQAAAABAAAAbqADAAQAAAABAAAAYgAAAAD4/R2+AAAACXBIWXMAABYlAAAWJQFJUiTwAAAbhklEQVR4Ae2dB3sTSbaGT8uAyTljwOQcBmZmd+997v33d+PsRJKzMQ6YZILJWH3ft9sNwkiyLckg7eOap0e4JXVX11fnnO+EKiUpLVZbx41AqeN6vNrhbARWgevQibAK3CpwHToCHdrtVYlbBa5DR6BDu70qcavAdegIdGi3VyVuFbgOHYEO7faqxK0C16Ej0KHdXpW4VeA6dAQ6tNtrOrTfn7ptVurDh4hXryJePI94zvGaf799FzH3PqKEUlmzNmLDhogtW/Nj86aItesiuro+XafD/tW5wM3NRbwHmNlZwHoa8fBxxINpjgcRz57l4L17m4PT3R2xdUvEnn0ceyP2cuzYGbENIAVwTecNQ+f1WMlQyt68jngyEzE8GDEyHDE6GjE1FTH9COBeABzvvwXYLiSuG3C2ImV7dkfs3x/R2xtx/ETEyZMR+wBzI+91mPQlHZUBF7AykvbkScS9sYi+vojbtyIGhyIm7nP+eZRfvIxkFkmb/RDlt3wWVVna0BXp1rWRAF6yA8nbD1gnAe/suYhz53Mg9+zJVWqSMDPav3WWxM1hy14iSUrX779E/PNfADcQ5f7xKE/PRBIAFin/AVjRymD9kj840ikAjO5Itt2LrnGkcwrV+hJVq8pdhx3UBnavL77Z1q+dA5zS9gziMYak/f2vgPZTpL/cRPKwbc9fABpkBFhgJHUGfC77XMp15n6ei9KTZ5G8hMhoJ0tI2snTuf3rALXZGcAVNm1yPOKPXyN+Rtr+uBPpzUmgQgIzSauD12dvfQA8JLf8PtLhNxlgicwzs3MMxwYkTslrc/A6Azjp/lOkTRLy078jfrsd5d/uARokpK6EfYbYgj8+5KAPTnI+iUQCs207BAZbtx7XYRW4BeO13D8LabsLAbl1O+IGoE0+jjKSljQMWtGJOcB7F8k93IfNsNNDB1CVALd9G0QFH0//r00bOqLN2xvU2WPs2MBARH8/DBJ1Oa1Nk4g001Q26wCuG61ZjjKMNCMr4/ciZvAL32gz27e1P3CzqMOJiYg7SNvQSHy495DBhiI21WSXawB/Q3ThHnQd3hKlTahHoy26Go+YKK+bvUdTHVz0y+1r41SR2jadakHrH4p0/OG8pMkel9u6+O5mbNjmSPZtj2QXBESVuJXXTTjg6yEl+4ioHD2C2uTvUnuHw9oXOEEz7nj37ry03Yvy8AxocX5ZTcnqjrS0IZIzuyPp2RfRezji4EGAIooieBsB1LBYxii35OGwNvfn2hc4Q1oT47ldu9UXZaRNFbm8uIZStiFKPTsiTvQQKTnFcYZw1/GIA4dyCZNBroWEGDGRSWZBaRim5KSNW3sC9x5bM4Ot6e+DlPTjbwHgw1lAWLq0STpKgnYBpnjqWMTVixFnzgHgyTzQrKSpImWOHRLmqpxH7QncS4iBti2LQ45EemcaaUMCl0z/c+JR6t0ZcZFoyPfXIv7yl4hjJwANVWk2oAPBam/gJCX3CRgrbbf7ICTT+GyvkLZ6oazKR8rVY3IO+3UJtfjf/xVx/XskDTVpGmepoNmPrBHsRHbbDej2kjiDvdq2sdE88g/9j3GDx6rIpQCXE5FSL070WaTrTz9GfPddxGmkbjvSVyvvJkjm9968ze+vK2BfypzfDHHJDkhLG7X2Au4tzvajRzjZONt9A5EOTEX6Ema5JNAMMXdFqXsjwWIo/dVLEf/zv6hHiMhu8nD1WgHaI5KwD5D2ImsgcEdhoIePYg8BsI3Ua/sA5+BJSO6QX7vTT1ySWOTMa8BYKiFZE11bd0RyHvZ47TLAXY04woArLdWa7oYS9uQhqnk6wgD25ARMFts6zd+yyl0AvgVJk4G2EWg+TnsAp6qyTmSa2W48cnA40lFt25slMsl1fA4/7QTE4zxqUfV4lgSpkia9r2xOkHew1qeEtR4C0PBQfgyNImnc/wFAPiVas5/vWtYgYOt4bbPWHsA5mE8e59H/mzciHZuMucfkypYobQkxx9JRbNg57NqfsWsXUJMHDn4Z4XeC6GooUbgZcetGxE0myvAI4bSJSHE50pfvcNaR3kNMgkNc48jhiJ2A2Gbt2wOXZbUhAw7e7TvYNiRgsshmA+giLQl8sR5AuwhrvAxgl1CTliZY1VU0ASvDDmeIvEyhDpkc8QfHDdQyk6Q8waR5SNkDmYKSMcz9sE+zBIcAbTvO+/ru4kpt8/rtgVNtaduGBnEBBiPtG8e2LSXPhg1CJq0hSY5C/XWwL1/B2cYFMP5YySCLkgez5zd/J4P+d4C7HekNfMQZpAyVLAHKozI47fsAS/APYts2b/n8Wm0C3bcFTkl4ihSYIL2tyrqLinzOAEIaFm36a9SPnESdXcaeXfseNonUbSUi8hloSO0LJsLYXcod/hbxt3/moA1Nx9zzQh1/kux0w1psIxJsNdh+pK4Npc2h+XbAFSQhi5AA2uAQKquI/i/GJAWNiq2Tu7BrgJWRESRtL1Ji3LGyWSQraD/9FPEvjt9uxtwfuBnlajk91ORmvr8D8HcBnrWXbZpM/XbAaXOKQb15K1Lof4xha5ZASLJc2kFU5KmjgIZ6vH4dEnEEXwu1VrTCrlkgqzT/318jfvmdkodRPlGLrcJAN8AgLZ7dThmDtSeV0ltcuw1evw1wDqol45mKhJDcwdmemsHWYO8WbTA+pCE510tkBPV4EdvWA2jdkJFKX8sqZmos4w7X/+VnbBvFRXcfzd+D+1dpToiSwOn7GYBet/5LZur31BZOPF8TwF7D0fV1h/Lr3q0YrLcMqoRkEEJiScIQ0vZQQlLftuUR/41IGqThwlnsGpJ2HBcgU2kLHsWJMcl1+2CON4l5DlARNoParDM5SkReEn02s+EmVtd1fT4Z7L9gGQ5TW1gtra9n4lXp/IptwdN+pTvPzublCEb/h0ajfNdc2+LSZpomOY7dOY89u3YNabucp2gW2jUl2vUDQ0yKW0ha/2jMAdripAf7th4gTKpmzjfALWxK2hsmxdQkkw1nXck8xET6jwbOAZWa60tZjkAVcjr+YB40ZnLNZo3I+iid2hPJhVNQf+yapeO7IScLWV+mhpEEbRvxzrjHAA88ATQnRr17GOtU7QGWE6FW6YL9n0UFm5k36iJwH7jubhio0vqVVObXlTjjgy9RibI8gYP+5+UI9aRNBrk2Sru2RXKsBzKClOlkHzuW+1iVdk3gXVugGjM1NDqCulSaVcPV7ZpfKVqpO8lDZGbCF163+FDxDFkBU38+cZTQ3l6YKBNpw9cZ0q9zl+KhXyEJE0oAknAHZ3u+YovhqtMEDhV5+mDur/35L+TWjucRjWqDqyqbgZ2qysYB79lLIGPCLCJtdqD8nvyCEmtWoFYTuFlUpdVgk9zjPX8rdSZpLYPwqNavWtdr8PzXA06DbjyyD5anChslQvJ4sXIE0jQB7b+EM3z5AgeSdup0dTJSDIDk4RkB5MePsEGwyGdveIdzS2kZU5QtAoaSW63N8b6kxCz9DHaUgEHmPpjV2EnEZdNGpI5jhdvXAc5Z7OKK6ancpxoYirkbSEPGImsMEAwvJXgcpyAj1ozoZKsiD/bkdqjWrJ7jXlaHIREpRa4GjZfaEqKV8Y4JZhhOu1WtCahFuq85Zkk74WIkm2Cg+KKZW7JTu7vyUvd1gHMmP0CtZBF5nO0Ja0jqlyMYzirtov7xLGrxh2swyEt57NDlULVAc6BTBjaTCAb1GZKxBIf+Ez4sBKGCOVGlm6tTLS60d05CzyuVvKYv+c7EoyjhcmQ1mbuZaDsAb7F+frppQ/+CRq1wy2zCPAsTuIFRmJ7Rfwe1+qzO1rDt2EpS9DCAwR6vkBQ9epSaEUJRdUFjUFVlSgwOePJcaePvJbayIOtjyhpfcQheLZUJgGlmC/nOJJKN6s9K5IeG8vir11nBtvISZzmCZGGQBzJC0jcRc5Qj1CMkmb/Ww6y9eA5/DdCuQP937ca/QiUt1lKAcrJwuCLVZY717lV5OQuSVK2JQelZ1O1r/E1dg0p3zou5ls4E7fwkSoPPDXCfozzjgQMkcem3EqcTv0JtZSVOoiAhMezkISF5ropkYKs2i32IjJzj4S/z8D/+mKdplhrsVSWryjyQhgTQliNxugzJrCRqJneu7bukqrIloKi/xpF0A46+H98rY6/Tu9jtfoiX+T6TtX7XvqxAWzngBE0DbjnALQw3ElemHCHNCEk14KT966npx66dPgZw2DTJiHFIWZq2ZqlNqWtowOZYdoyKewwr1YE3MvJ+gcpzMwCTtBs5jLJkwJnLex9lHH1907hxM1+jLklyHFagrRxwmT8FJR8d5kGYgSMTDAQDUsOuoXci2cqCjNOH8gqt6z9E9B7Pk6Ir8OC1LikAMUm/J2HAFhFZLlg5CcwWWEBkIBrw0o8RFgGajfIYgMswBwdzFq3aXoG2MsA5y1wUPzySq0hX2tx/Oi9t1WYgg1FC0iQjP0D79des7zd4u9y0CsKWOdDZYC9fTaUAN+dCx2mkzbULljtop4umzTNZO79PSmmzNKHQBrDM8RcEtMfwVfuwe4DnHiwL1W1xrSZeVwY4Uyo+8BAdx2crsxjREgEYQ5WuateIQ57Zg1EHLItYNe4H9mNHCCXVY5FVrqa9yVvxWvVDdU5KaF6hHVB79wBOlSnLLJqJVQPK5utIuKabVZcFcH4XN+Q2kjrIpB0APG2dmYoWt5UBzsj83dH5cgRep5W2illb8RCCFgfJr2XB46s5gxQ012QvGzQuLF5KW4Zb9r+Kuy3ln9orJIcqsww4wZMVF01ba3RkJ/4aTDfZTWSHkFzRDGaXXXh5l+9Zaugq2sdIb6W6LT7cxGtrgdP5NapgYalBZFRFvjxK0BZKm5ERJArQSud682KfCxfzyioLdGRvy24CRR+K0BVDmDPL5V6Iazxi8CVWqkuXMqv+HXwnk1LnOgQWQiY43Ml2gPzY5oGfQGKHRxkH7J1FSmzpkbkpHz/X3D9aC5xhInNtRv810Or6MVRmVUJiHHIj9ZB7YY/nCWldy1Wk5XDmwhpp4ubg6oRnjrMnGmvpc4LTRESyVUPGPX02J0TRtmDnXBhpQdFubPFnDZXpOvJRQ3yoSwnaE65hTWeLWuuAc8AMvI7QSX02a//Z7ae6ipT6A9qlgxARQNOuua/WDkBrpukGSATeIeEMUjmbMBWDvYxrW2MZMzzPYyTH4xUTsjJ+qcTpbO9H6nZs5sprOD5pCTMSc/f4Tv9IlsyNQVSmUtci96B1wElIdFizsBYpG+i/0f9q5QgZaK5dO39q3l+7xOwFRDeJaaZJvaXvxipZiJ9R+9zYLfuqmZ2b4ZncX8USQnc1+gCYRbOvburmJm4skjS2ih4t3uUVO1l+Fekw6lai4mR2QYml9i1orQNO5mUOLHO2KTQdLJzthb1kVu5DzZzsoTrrO8gIh/6aOa1GyEjl5Y0PvmCyeOj8Z6Ch4hpqfo+JoOqXbEnrjYEWzQzANiafJYEQlYRVQsmCakdLJeaU1lFMh5VmmhDXLLSgNQ+cKtKZblLxTh8qkqW/ZJ0zVbPAtqWyr9KOnIxcu4Jt4zh8OI9BLicyUuvBnc0yOAeL0Fp121rry9XOo2YNNDspPSqdaftrBMWdiPZxHFHNK3WVbT6ich+JxS3KwRvLCVyTKrN54HwYbdvYKKBRmDM4it9m9J/znwGXxyFL55mhqsjr11iTfSYv9tHJblbanEBKx/QDVJIJVP7ddOOaSnGWf2MiVA62/dVlsdaEjUuTPTsitbTvi4bkTj1DZc5P7GE4gKq3SaLSPHDaFFWk5Qgs2CiPWPzjoKlqPrXcyd5FNvs0DBJ/LavQ4qFVOc22QuqfotKk74aqJiACrWjvkLoiubowxaNbYOLUBSJ7UJeZM/7lTY3PZrU1A4DG5M5qYSqd+i+/suiZxoFzsATNyEA/nXHNNtXICTUen0f/ZZAkRY9SoXXmeF51fPZCvgyqVZlipV47ZPXYGAsiH+Hwv20NCYiE56wVtLYizN0bBG/H9ihtVOI+MctPo8/SLQMQY4zVEOBJVLSZTbTGgdOncYaP30N30xGY01xGSDTgn6TNCi1ZZByDNZoU/f6HfMsK/bXlxiFrPaiM1kWK7hp7dyzSB7UjNbUuUfN8ikrM8m8Cwr8rm1XMBgtM8AJgukEbVw04v4l7MgrrttReotIkSWkcOH2a0aGcRRpMncKuZPtffQLNh0gTQkJXevKIv0WsJ/DXnKXN2rRiAJU2E5+D9EUCkO2JgiZo0A0oLvvxdR321/yb9mzh6lb/Nui8kYnJegNrT1xkWb2Z0iWO+QDiNDKa97n6B5d0tgngkKwhADNCQlyu/NAlS8z8j9ImGdnMBjF7YY9nof2XiYxARqw9NHjcqmYNpXbN0BJSn448gtEKXOUEavRmDI+Ew9ybx8KVO04+C2Ctq1TtZ4lV/q4qdfYHqdO3tWywycCzd2msGaGQkLBdU3qfotNpbcqnwXIHhOQAdSMnj5LJRj2aqjnSm6fzWyVt2lnjiE4gkpfp8BiJ0KdMmE/9aOzhim+h9pSmzVvJCKAlFgLnx3wWVb6gUa7gMmRmTs2WUC5Yvk9xUWWqqOana7/ROHDGA2Fv6dhUFhpS2hjGrGUMEmOdXDoBgwQwWaRrsvV7WgWaxMh44M0/8rVvfcNsQDrD/QWtFcCpMQDDbe+tlzQHl0lU/oyf/187CMjawkUbRUwPXuahuUU/W/sDjQMnNaYgNB1+wtUpUTNznDUkbROSdmJ/HjxW0k6jIrdurz5j57+1rBf3lSz2Q/n1V1aY3oRusxqH3xtolbRpq5L9TDTTNx7GJqtJnB232suJPOfULaZv9SfKqqopj0gqfcLqH617tnHgVFOElfJNP9UNdljqD4s8uptFGaeh/t/jbF/EruHnLDTsdbtV503vK5UeGWJZ8N8i/v1rlH/n3x9tbJ3vLuMtF5nEHsDay7O4uERtUW1Bh/0pQ5A0HZSjJ7BtR6J2810+7/eaaI0Dp1ZA7VlLlcwXzKSAVkJFxonDSBu+2slTeUioFeEsH9RaRzPrt26yE/rPEf/4iTKBUcJtSP5nxKiJEcm+ygTsgeYfPoBdPgpwECxBW6jm7ZOs1uiKfVMTZJoHbVSzOXCoVUatmdY4cN4YimwNZJnO2o2SsToSo3GMhz0PcD0AqG1opjk4Vg0bdrqPPTVt9Pd/ABwq8meqoimurRapafyWa7geq17deeF4b16Ia1hrIWjeQF9WH9KQ33P3SKGPH02GH6jWcq2U/XRMtbeXeK5x4DTGbEtROgwJeUL6gs4bqysd3Jevx3ZNtpVQzapIw01S/myrixssC/4Fmwb1H2CJ1j18R/NmLSEj+Yi5XqFLP/PIIdQ9ttnnqJUnFDgzEcYe0QTJa0JbWYy29uhrStKDZBKqqd3aX/vincaBs77Q7d6PwxY3MoB96HdjdTtRlcbu3I6poWIf+qjhdibP4lj7C1VFdMaUETX61me6ic3y9rD84tm/OGEpRReTMbmApjiLjT6N/+mvX9XyO1WT5iDtI2QpnVXi6qlJTFtpfXTtZYwWLsj8ojf1TzQOnL6L+v/EJGoSS/cUdbGWc9RGxrZ5+ryc7XFViTJVGVpG9Z8A2HgeA80Aux0pa8XTvilmtUlSBm2RQar/6AvftZQC6n8EImLp+yVI1WnA03+rZaPNzwnaJA71NL+F8Fjpr9dQk/sgPfu5x1LK6etcqnHgDPX4YKoxZl7yAHXhz34JVrYLgQZ4CU3pMnxmuEy26Nbx2rJ7gDY6inM9wisbabMHSkxSswgJySl//Zm9hDt//Ei+KQA7Cl3tIVAAaJa+u1R5J5rDNQDVmkTE/hofHZ/IfsSi0pf98it5cVTXbqStF/W7hQneRGscOHW0K2hmXwEeGQFXmj4GPCVGFSI91qCbd/Lfni8kSrLh4XkTlSZAXeH58AHgcB0lzbXb/uKUSdnRGaSsWHPQOsBkd9L+ru3Q/iOo9quA5TbAV65gBgDRMrxqpMQBV43bV/NrbpU45aSqJXHex20+AO0w/q2LM5skbU0Ah0RZJ/JOaWHgTcvbJBOyLA8BFBilMvNzeDBtl2UFVjr78EY/PB4hUfcBbopozASvo09i7q0pIgdDp6OVgGU95X+4MhCo5AzPoaT9+U/4nj/kW3BYU1ILNNW6lV/DA3nGn+hRzmw5X6OVmCDJMYjb6ZOo4UsE2nfW+OTSTjcOnA+lWtyFPTOTPTWRxyEFyGom1Z0/MlRssOZielMZqhhtmL8DJ3DQ6KwQx3I4JDd9xiR4yHsEivNin1YDJt1HyvjBiETXxViqRCSL8PCqC2PAuBYbNsboRDOo/cuvBLZht+P8zVW/tLmaC2znJpj3qQNI81XCf9/BC058Q1VJlzKjbT7KhzWjbUhIyTOSYPBXO2iCU5Vizg5bkAH1Cql7xQC4FJdVo+lzAq8Z4VC6Wg1UPnh5IQ9hrO2Asg/QevZHHMPWmCN0W3snn0w4K8ZlUlZrqn1Z5NAgLsnvmVtSHr1POsu17Av7zb1wLdJt7Dl2jvFxz7EfkGbHyR1nHZsmWuMSV9xUdqm/5oMbFtqsXcBVMG2hqpRpGudTEslFpX3EFAGKE4BlMQ2+EEdecbzw4YubNPpagNYNref3cw4BzMG92DMG8iSzXnJ1nFcLW7fQRzVIPfVYaA/3BfuJUNutEbTDc/ruhKtsOtmQHXzcOMXkcEvG69dRkUhcJtEwy1r3qbxMnX83D5wdkC67CILuZg+vzTMMpp3wZ0+URG0evl/i4Ew/ifIDAsL8jmljJeKfP5EW0HuXur0nRICtCxPKCBJ9JSeSm6rtRi0eBKCeHggCg+nur2YsLLGThDgBazUlzf4btTF73d8PYEgeDri/u5q+Z8J6/42o4U3cly2lkn27uBfq0V8XOXeB17P5/VyB1CRodrNOb2s9RY3z2oXdAOQixFfYLkmJtZJmj1UNLqt1kMhtJdQZdpkSes2AGH1ospU0LwYEzFYDViJY0m0l3XoQVaBBAYHyN3WoyspybEtd6qu/xt6WWTm6G9NYJMsELB3guvvJPBaT13tvY5KYBjrCBDl+DKlGE7k408JZJ3ALQHO4WgecV1PynL3EMLMCGw28oTE723uC9xhMfzHK8BVFRomG3nRIs808mPfI1l1zf/tABCSvBWGyGPh2MeIGJpJSaMZayV9W4/qSrWzdHteWHevSWJOSAcerk9f6k11MFjcqdYK4js7J3ELQ7PbK/Zy0lDm7Aw9k82/ZpAVGLltyma0qSP+uFU3wupjRGn3BcRAdMCeLRTwuJHEiNTLjZcLWbLpwQ9dGbVI8X9H3Lu7vPbTzThJtphPFydTIPYvr1nhdOeBq3HD1dGtGgCm42jpxBFaB60TU6PMqcKvAdegIdGi3VyVuFbgOHYEO7faqxHUocP8Pu8XQKhMSYmcAAAAASUVORK5CYII="
)


def initialize_datasource_catalog_schema() -> None:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS piflow_datasource_type (
                        id BIGSERIAL PRIMARY KEY,
                        type_code TEXT NOT NULL UNIQUE,
                        type_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        logo TEXT NOT NULL DEFAULT '',
                        enabled BOOLEAN NOT NULL DEFAULT TRUE,
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        capabilities_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                        init_fields_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                        extra_meta_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_piflow_datasource_type_enabled_sort
                    ON piflow_datasource_type(enabled, sort_order)
                    """
                )
                _seed_builtin_dataspace_type(cursor)


def list_datasource_types() -> list[dict[str, Any]]:
    initialize_datasource_catalog_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    type_code,
                    type_name,
                    category,
                    description,
                    logo,
                    enabled,
                    sort_order,
                    capabilities_json,
                    init_fields_json,
                    extra_meta_json,
                    created_at,
                    updated_at
                FROM piflow_datasource_type
                ORDER BY sort_order ASC, created_at ASC
                """
            )
            return list(cursor.fetchall())


def get_datasource_type_by_code(type_code: str) -> dict[str, Any] | None:
    initialize_datasource_catalog_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    type_code,
                    type_name,
                    category,
                    description,
                    logo,
                    enabled,
                    sort_order,
                    capabilities_json,
                    init_fields_json,
                    extra_meta_json,
                    created_at,
                    updated_at
                FROM piflow_datasource_type
                WHERE type_code = %s
                """,
                (type_code,),
            )
            return cursor.fetchone()


def _seed_builtin_dataspace_type(cursor) -> None:
    init_fields = [
        {
            "name": "base_url",
            "label": "服务地址",
            "type": "string",
            "required": True,
            "default": "",
            "placeholder": "请输入 Dataspace 服务地址",
            "secret": False,
            "options": [],
            "description": "Dataspace 开放接口服务地址",
        },
        {
            "name": "app_id",
            "label": "应用ID",
            "type": "string",
            "required": True,
            "default": "",
            "placeholder": "请输入应用ID",
            "secret": False,
            "options": [],
            "description": "Dataspace 开放接口应用ID",
        },
        {
            "name": "auth_code",
            "label": "授权码",
            "type": "password",
            "required": True,
            "default": "",
            "placeholder": "请输入授权码",
            "secret": True,
            "options": [],
            "description": "Dataspace 开放接口授权码",
        },
        {
            "name": "space_name",
            "label": "数据空间名称",
            "type": "string",
            "required": True,
            "default": "",
            "placeholder": "请输入数据空间名称",
            "secret": False,
            "options": [],
            "description": "系统将根据空间名称自动解析 space_id",
        },
        {
            "name": "ftp_user",
            "label": "FTP用户名",
            "type": "string",
            "required": True,
            "default": "",
            "placeholder": "请输入FTP用户名",
            "secret": False,
            "options": [],
            "description": "用于访问 Dataspace FTP 目录",
        },
        {
            "name": "ftp_password",
            "label": "FTP密码",
            "type": "password",
            "required": True,
            "default": "",
            "placeholder": "请输入FTP密码",
            "secret": True,
            "options": [],
            "description": "用于访问 Dataspace FTP 目录",
        },
        {
            "name": "logo",
            "label": "Logo",
            "type": "string",
            "required": False,
            "default": "",
            "placeholder": "可选，未填写时默认使用空间Logo",
            "secret": False,
            "options": [],
            "description": "可选的 Base64 Logo 字符串",
        },
    ]
    capabilities = ["list", "download", "upload"]
    extra_meta = {
        "builtin": True,
        "instance_api_prefix": "/dataspace/source",
        "supports_validation": True,
    }

    cursor.execute(
        """
        INSERT INTO piflow_datasource_type (
            type_code,
            type_name,
            category,
            description,
            logo,
            enabled,
            sort_order,
            capabilities_json,
            init_fields_json,
            extra_meta_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (type_code) DO UPDATE SET
            type_name = EXCLUDED.type_name,
            category = EXCLUDED.category,
            description = EXCLUDED.description,
            logo = EXCLUDED.logo,
            enabled = EXCLUDED.enabled,
            sort_order = EXCLUDED.sort_order,
            capabilities_json = EXCLUDED.capabilities_json,
            init_fields_json = EXCLUDED.init_fields_json,
            extra_meta_json = EXCLUDED.extra_meta_json,
            updated_at = now()
        """,
        (
            DATASPACE_TYPE_CODE,
            "DataSpace",
            "file",
            "Dataspace 数据空间类型，用于访问空间目录并进行文件下载与上传。",
            DATASPACE_TYPE_LOGO,
            True,
            1,
            Json(capabilities),
            Json(init_fields),
            Json(extra_meta),
        ),
    )
