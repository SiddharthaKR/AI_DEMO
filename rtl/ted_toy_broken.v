// ted_toy_broken.v - DEMO BUG VARIANT of toy Mueller-Muller CDR loop, OSR = 2, one symbol per clock.
// Verilog-2005 (iverilog -g2005). tau = fixed Q4.16 in SAMPLES, wrapped to [0, 2).
//   y_k = x[n] + mu*(x[n+1]-x[n]),  n = 2k + floor(tau),  mu = frac(tau)
//   e_k = a_{k-1}*y_k - a_k*y_{k-1},  a = sign(y)
//   v  += e ;  tau += (e >>> KP_SHIFT) + (v >>> KI_SHIFT)   (full-precision integrator)
module ted_toy #(
    parameter KP_SHIFT = 8,
    parameter KI_SHIFT = 16,
    parameter signed [19:0] TAU0_Q = 20'sd0
)(
    input  wire               clk,
    input  wire               rst,
    input  wire               en,
    input  wire        [5:0]  x0,        // mem[rd_addr]   (unsigned 6-bit)
    input  wire        [5:0]  x1,        // mem[rd_addr+1]
    output wire       [15:0]  rd_addr,
    output reg signed [19:0]  tau_q      // Q4.16 samples
);
    localparam signed [39:0] WRAP = 40'sd131072;       // 2.0 samples in Q.16

    reg  [15:0]        k;
    reg  signed [39:0] v;                              // integrator keeps full precision
    reg  signed [24:0] y_prev;
    reg                a_prev_neg;
    reg                first;

    // NCO split: integer part -> pointer, fraction -> mu
    wire               tau_int = tau_q[16];
    wire        [15:0] mu      = tau_q[15:0];
    assign rd_addr = {k[14:0], 1'b0} + tau_int;

    // centering: unsigned 6-bit - 32 == flip the MSB
    wire signed [6:0]  x0s = $signed({~x0[5], ~x0[5], x0[4:0]});
    wire signed [6:0]  x1s = $signed({~x1[5], ~x1[5], x1[4:0]});

    // linear interpolator (Q.16)
    wire signed [7:0]  d    = x1s - x0s;
    wire signed [24:0] prod = d * $signed({1'b0, mu});
    wire signed [24:0] y    = ($signed(x0s) <<< 16) + prod;
    wire               a_neg = y[24];

    // MM TED
    wire signed [26:0] ya  = a_prev_neg ? -y      : y;
    wire signed [26:0] ypa = a_neg      ? -y_prev : y_prev;
    wire signed [26:0] e   = first ? 27'sd0 : (ypa - ya);   // MM TED  <-- BUG: sign flipped

    // PI + NCO with wrap
    wire signed [39:0] v_next   = v + e;
    wire signed [39:0] tau_next = tau_q + (e >>> KP_SHIFT) + (v_next >>> KI_SHIFT);
    wire signed [39:0] tau_wrap = (tau_next >= WRAP) ? tau_next - WRAP :
                                  (tau_next <  0)    ? tau_next + WRAP : tau_next;

    always @(posedge clk) begin
        if (rst) begin
            k <= 0; v <= 0; y_prev <= 0; a_prev_neg <= 1'b0; first <= 1'b1;
            tau_q <= TAU0_Q;
        end else if (en) begin
            k <= k + 1'b1; v <= v_next; y_prev <= y; a_prev_neg <= a_neg; first <= 1'b0;
            tau_q <= tau_wrap[19:0];
        end
    end
endmodule
