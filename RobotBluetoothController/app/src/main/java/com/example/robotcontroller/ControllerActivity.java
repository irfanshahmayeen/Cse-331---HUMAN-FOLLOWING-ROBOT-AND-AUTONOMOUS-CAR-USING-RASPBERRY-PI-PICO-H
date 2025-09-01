package com.example.robotcontroller;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.os.Bundle;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.IOException;
import java.io.OutputStream;
import java.util.UUID;

public class ControllerActivity extends AppCompatActivity {

    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    private BluetoothSocket socket;
    private OutputStream output;
    private TextView status, connectedDevice, deviceId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_controller);

        status = findViewById(R.id.txtStatus);
        connectedDevice = findViewById(R.id.txtConnectedDevice);
        deviceId = findViewById(R.id.txtDeviceId);

        String address = getIntent().getStringExtra("device_address");
        String name = getIntent().getStringExtra("device_name");
        connectedDevice.setText("Connected to " + name);
        deviceId.setText("Device ID: " + address);

        connect(address);

        bindButton(R.id.btnUp, "F");      // Forward
        bindButton(R.id.btnDown, "B");    // Backward
        bindButton(R.id.btnLeft, "L");    // Left
        bindButton(R.id.btnRight, "R");   // Right
        bindButton(R.id.btnStop, "S");    // Stop

        findViewById(R.id.btnSpeed1).setOnClickListener(v -> send("1"));
        findViewById(R.id.btnSpeed2).setOnClickListener(v -> send("2"));
        findViewById(R.id.btnSpeed3).setOnClickListener(v -> send("3"));
    }

    private void bindButton(int id, String command) {
        ImageButton btn = findViewById(id);
        btn.setOnClickListener(v -> send(command));
    }

    private void connect(String address) {
        status.setText("Connecting...");
        try {
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            BluetoothDevice device = adapter.getRemoteDevice(address);
            socket = device.createRfcommSocketToServiceRecord(SPP_UUID);
            adapter.cancelDiscovery();
            socket.connect();
            output = socket.getOutputStream();
            status.setText("Connected and ready to send commands");
        } catch (IOException e) {
            status.setText("Failed to connect");
            Toast.makeText(this, "Connection error: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void send(String message) {
        if (output == null) {
            Toast.makeText(this, "Not connected", Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            output.write(message.getBytes());
        } catch (IOException e) {
            Toast.makeText(this, "Send failed: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            if (output != null) output.close();
            if (socket != null) socket.close();
        } catch (IOException ignored) {}
    }
}