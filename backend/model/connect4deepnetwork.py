import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset


class ConnectFourDeepNet(nn.Module):
    def __init__(self):
        super(ConnectFourDeepNet, self).__init__()
        self.fc1 = nn.Linear(42, 300)
        self.fc2 = nn.Linear(300, 700)
        self.fc3 = nn.Linear(700, 300)
        self.fc4 = nn.Linear(300, 3)

    def forward(self, x):
        x = self.fc1(x)
        x = F.relu(x)

        x = self.fc2(x)
        x = F.relu(x)

        x = self.fc3(x)
        x = F.relu(x)

        x = self.fc4(x)
        x = F.log_softmax(x, dim=-1)
        return x


class ConnectFourDataset(Dataset):
    def __init__(self, rawdata):
        rawdata = np.array(rawdata)
        rawlabels = rawdata[:, 42]
        rawdatabase = rawdata[:, :42]
        self.labels = torch.from_numpy(rawlabels)
        self.database = torch.from_numpy(rawdatabase)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        data = self.database[idx]
        label = self.labels[idx]
        return data.float(), label.long()


def train(epoch):
    network.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        optimizer.zero_grad()
        output = network(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % 200 == 0:
            print(
                "Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}".format(
                    epoch,
                    batch_idx * len(data),
                    len(train_loader.dataset),
                    100.0 * batch_idx / len(train_loader),
                    loss.item(),
                )
            )


def test():
    network.eval()

    test_loss = 0
    correct = 0
    size = len(test_loader.dataset)
    num_batches = len(test_loader)

    with torch.no_grad():
        for data, target in test_loader:
            output = network(data)
            test_loss += F.nll_loss(output, target).item()
            correct += (output.argmax(1) == target).type(torch.float).sum().item()

    test_loss /= num_batches
    averagecorrect = correct / size
    print(
        f"Test Error: \n NumCorrect: {(int(correct))}/{(size)}, Accuracy: {(100*averagecorrect):>0.1f}%, Avg loss: {test_loss:>8f} \n"
    )


if __name__ == "__main__":

    batch_size_train = 100
    batch_size_test = 1000

    training_data_file = np.loadtxt(
        "./c4_game_database.csv",
        delimiter=",",
        dtype=float,
        skiprows=1,
        max_rows=300000,
    )
    test_data_file = np.loadtxt(
        "./c4_game_database.csv", delimiter=",", dtype=float, skiprows=300000
    )

    training_data = ConnectFourDataset(training_data_file)
    test_data = ConnectFourDataset(test_data_file)
    train_loader = torch.utils.data.DataLoader(
        training_data, batch_size=batch_size_train, shuffle=True
    )
    test_loader = torch.utils.data.DataLoader(
        test_data, batch_size=batch_size_test, shuffle=True
    )

    learning_rate = 0.01
    momentum = 0.5
    network = ConnectFourDeepNet()
    optimizer = optim.SGD(network.parameters(), lr=learning_rate, momentum=momentum)

    epochs = 15
    test()
    for t in range(epochs):
        print(f"Epoch {t+1}\n-------------------------------")
        train(t + 1)
        test()
    print("Done!")

    torch.save(network, "test_model.pth")
