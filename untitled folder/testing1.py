def add_dataset(new_data, current_database=[]):
    current_database.append(new_data)
    return current_database

batch_1 = add_dataset(95)
batch_2 = add_dataset(102)

print("Batch 1:", batch_1)
print("Batch 2:", batch_2)
