old = ("        uint8_t x = OLED[oled_rank_count].X_LEN;\n"
       "        uint8_t y = OLED[oled_rank_count].Y_LEN;\n"
       "\n"
       "\n"
       "        if(SIM[i].state != 8)\n")

new = ("        uint8_t x = OLED[oled_rank_count].X_LEN;\n"
       "        uint8_t y = OLED[oled_rank_count].Y_LEN;\n"
       "\n"
       "\n"
       "        SIM[i].flag   = 1;\n"
       "        SIM[i].mode   = (i == 0) ? 4 : 5;\n"
       "        SIM[i].net    = 0;\n"
       "        SIM[i].signal = 4;\n"
       "        SIM[i].state  = 1;\n"
       "\n"
       "        if(SIM[i].state != 8)\n")

open(r'D:\Codebuddy\toolbox\_tmp_sim_force_old.txt', 'wb').write(old.encode('utf-8'))
open(r'D:\Codebuddy\toolbox\_tmp_sim_force_new.txt', 'wb').write(new.encode('utf-8'))
print('CR in old?', b'\r' in old.encode(), 'new?', b'\r' in new.encode())
print('bytes', len(old.encode('utf-8')), len(new.encode('utf-8')))
