// tb_ted.v - reads unsigned 6-bit samples (one per line), runs ted_toy,
// dumps tau_q (signed Q4.16, samples) once per symbol.
// iverilog -g2005 -P tb_ted.N_SYM=.. -P tb_ted.KP_SHIFT=.. -P tb_ted.KI_SHIFT=.. -P tb_ted.TAU0_Q=..
// vvp sim.vvp +STIM=data/stim.txt +OUT=out/rtl_tau.txt
`timescale 1ns/1ps
module tb_ted;
    parameter N_SYM = 4000, KP_SHIFT = 8, KI_SHIFT = 16;
    parameter signed [19:0] TAU0_Q = 0;

    reg  [5:0] mem [0:65535];
    reg  clk = 0, rst = 1, en = 0;
    wire [15:0] rd_addr;
    wire signed [19:0] tau_q;
    integer fd, fo, cnt, val, k, r;
    reg [1023:0] stim_path, out_path;

    ted_toy #(.KP_SHIFT(KP_SHIFT), .KI_SHIFT(KI_SHIFT), .TAU0_Q(TAU0_Q)) dut (
        .clk(clk), .rst(rst), .en(en),
        .x0(mem[rd_addr]), .x1(mem[rd_addr + 16'd1]),
        .rd_addr(rd_addr), .tau_q(tau_q));

    always #5 clk = ~clk;

    initial begin
        if (!$value$plusargs("STIM=%s", stim_path)) stim_path = "data/stim.txt";
        if (!$value$plusargs("OUT=%s",  out_path))  out_path  = "out/rtl_tau.txt";
        fd = $fopen(stim_path, "r");
        if (fd == 0) begin $display("ERROR: cannot open stim"); $finish; end
        cnt = 0;
        while (!$feof(fd)) begin
            r = $fscanf(fd, "%d\n", val);
            if (r == 1) begin mem[cnt] = val[5:0]; cnt = cnt + 1; end
        end
        $fclose(fd);
        fo = $fopen(out_path, "w");

        @(negedge clk); rst = 0; en = 1;
        for (k = 0; k < N_SYM; k = k + 1) begin
            if (rd_addr + 1 >= cnt) k = N_SYM;             // out of samples
            else begin
                $fwrite(fo, "%0d\n", tau_q);               // tau used for symbol k
                @(negedge clk);
            end
        end
        $fclose(fo);
        $display("tb_ted: %0d samples read, done", cnt);
        $finish;
    end
endmodule
