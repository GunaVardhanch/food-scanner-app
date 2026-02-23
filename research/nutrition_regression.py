import torch
import torch.nn as nn
from torchvision import models

class NutritionRegressor(nn.Module):
    def __init__(self, num_outputs=4):
        super(NutritionRegressor, self).__init__()
        # Use EfficientNet-b0 as the backbone
        self.backbone = models.efficientnet_b0(weights='DEFAULT')
        
        # Modify the classifier for regression
        # EfficientNet-b0 original cf: (classifier): Sequential( (0): Dropout(...) (1): Linear(in_features=1280, out_features=1000, ...) )
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Linear(512, num_outputs) # Outputs: Calories, Fat, Sugar, Protein
        )

    def forward(self, x):
        return self.backbone(x)

def train_regression_model():
    print("Nutrition Regressor (EfficientNet-b0) initialized.")
    model = NutritionRegressor()
    
    # Placeholder for loss and optimizer
    # criterion = nn.MSELoss()
    # optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    
    print("Ready for training on NutriGreen/Nutrition5k datasets.")

if __name__ == "__main__":
    train_regression_model()
